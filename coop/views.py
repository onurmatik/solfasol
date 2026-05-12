import calendar as python_calendar
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from calendar.services import DELIVERY, ORDER_DEADLINE, list_calendar_entries
from members.services import get_profile

from .forms import MemberOfferIntentForm
from .models import MemberOfferIntent, ProcurementOffer


WEEKDAY_LABELS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


def _parse_anchor_date(value):
    if not value:
        return timezone.localdate()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return timezone.localdate()


def _add_months(value, amount):
    month_index = value.month - 1 + amount
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, python_calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _entry_tone(entry):
    if entry.event_type == DELIVERY:
        return "success"
    if entry.event_type == ORDER_DEADLINE:
        return "warning"
    return "info"


def _entry_time_label(entry):
    if entry.is_all_day:
        return "Tüm gün"
    return timezone.localtime(entry.starts_at).strftime("%H:%M")


def _entry_week_title(entry):
    if entry.event_type == DELIVERY:
        return "Teslimat"
    if entry.event_type == ORDER_DEADLINE:
        return "Deadline"
    return entry.title


def _decorate_entries(entries):
    return [
        {
            "entry": entry,
            "tone": _entry_tone(entry),
            "time_label": _entry_time_label(entry),
            "week_title": _entry_week_title(entry),
        }
        for entry in entries
    ]


def _entries_by_date(entries):
    entries_by_date = {}
    for entry in entries:
        local_date = timezone.localtime(entry.starts_at).date()
        entries_by_date.setdefault(local_date, []).append(entry)
    return entries_by_date


def _build_calendar_grid(entries, anchor_date, view_mode):
    entries_by_date = _entries_by_date(entries)

    if view_mode == "week":
        week_start = anchor_date - timedelta(days=anchor_date.weekday())
        raw_weeks = [[week_start + timedelta(days=offset) for offset in range(7)]]
        current_start = week_start
        current_end = week_start + timedelta(days=6)
    else:
        anchor_date = anchor_date.replace(day=1)
        raw_weeks = python_calendar.Calendar(firstweekday=0).monthdatescalendar(anchor_date.year, anchor_date.month)
        current_start = anchor_date
        current_end = anchor_date.replace(day=python_calendar.monthrange(anchor_date.year, anchor_date.month)[1])

    today = timezone.localdate()
    weeks = []
    for week in raw_weeks:
        days = []
        for day in week:
            day_entries = entries_by_date.get(day, [])
            days.append(
                {
                    "date": day,
                    "is_current_period": current_start <= day <= current_end,
                    "is_today": day == today,
                    "entries": _decorate_entries(day_entries[:3]),
                    "extra_count": max(len(day_entries) - 3, 0),
                }
            )
        weeks.append(days)
    return weeks


def _build_week_cards(entries, anchor_date):
    entries_by_date = _entries_by_date(entries)
    week_start = anchor_date - timedelta(days=anchor_date.weekday())
    today = timezone.localdate()
    days = []

    for offset in range(7):
        day = week_start + timedelta(days=offset)
        decorated_entries = _decorate_entries(entries_by_date.get(day, []))
        days.append(
            {
                "date": day,
                "weekday_label": WEEKDAY_LABELS[day.weekday()],
                "is_sunday": day.weekday() == 6,
                "is_today": day == today,
                "primary_entry": decorated_entries[0] if decorated_entries else None,
                "entries": decorated_entries,
                "extra_count": max(len(decorated_entries) - 1, 0),
            }
        )
    return days


def _week_summary_entries(week_days):
    return [item for day in week_days for item in day["entries"]]


def _calendar_navigation(anchor_date, view_mode):
    if view_mode == "week":
        return anchor_date - timedelta(days=7), anchor_date + timedelta(days=7)
    month_anchor = anchor_date.replace(day=1)
    return _add_months(month_anchor, -1), _add_months(month_anchor, 1)


def _upcoming_entries(entries, limit=6):
    today_start = timezone.make_aware(
        datetime.combine(timezone.localdate(), time.min),
        timezone.get_current_timezone(),
    )
    return _decorate_entries([entry for entry in entries if entry.starts_at >= today_start][:limit])


def _save_member_offer_intent(request, offer, form):
    intent = form.save(commit=False)
    intent.member = request.user
    intent.offer = offer
    try:
        intent.full_clean(validate_unique=False)
    except Exception as exc:
        form.add_error(None, exc)
        return False

    MemberOfferIntent.objects.update_or_create(
        member=request.user,
        offer=offer,
        defaults={
            "quantity": intent.quantity,
            "delivery_point": intent.delivery_point,
            "note": intent.note,
        },
    )
    return True


def _format_tl(value):
    return f"{value:,}".replace(",", ".")


def _payment_quantity_from_form(form, existing_intent):
    fallback = existing_intent.quantity if existing_intent else 1
    raw_quantity = form["quantity"].value()
    if raw_quantity in (None, ""):
        return fallback
    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        return 0
    return quantity if quantity > 0 else 0


def _offer_progress_percent(offer):
    if not offer.target_quantity:
        return 0
    return min(round((offer.total_quantity / offer.target_quantity) * 100), 100)


def dashboard(request):
    active_offers = list(
        ProcurementOffer.objects.filter(status=ProcurementOffer.Status.OPEN)
        .select_related("product", "source")
        .prefetch_related("intents")
        .order_by("deadline")
    )
    user_intents = {}
    if request.user.is_authenticated and request.user.is_active:
        user_intents = {
            intent.offer_id: intent
            for intent in MemberOfferIntent.objects.filter(member=request.user, offer_id__in=[offer.pk for offer in active_offers])
            .select_related("delivery_point")
            .order_by("-created_at")
        }

    calendar_view = request.GET.get("calendar_view")
    if calendar_view not in {"month", "week"}:
        calendar_view = "week"
    calendar_anchor = _parse_anchor_date(request.GET.get("date"))
    calendar_entries = list_calendar_entries()
    prev_calendar_date, next_calendar_date = _calendar_navigation(calendar_anchor, calendar_view)
    offer_cards = []
    for offer in active_offers:
        intent = user_intents.get(offer.pk)
        offer_cards.append(
            {
                "offer": offer,
                "intent": intent,
            }
        )
    week_start = calendar_anchor - timedelta(days=calendar_anchor.weekday())
    week_end = week_start + timedelta(days=6)
    calendar_week_days = _build_week_cards(calendar_entries, calendar_anchor)

    context = {
        "active_offer_count": len(active_offers),
        "calendar_anchor": calendar_anchor.replace(day=1) if calendar_view == "month" else calendar_anchor,
        "calendar_entries": _upcoming_entries(calendar_entries),
        "calendar_next_date": next_calendar_date,
        "calendar_prev_date": prev_calendar_date,
        "calendar_selected_date": calendar_anchor,
        "calendar_view": calendar_view,
        "calendar_week_end": week_end,
        "calendar_week_days": calendar_week_days,
        "calendar_week_summary": _week_summary_entries(calendar_week_days),
        "calendar_week_start": week_start,
        "calendar_weeks": _build_calendar_grid(calendar_entries, calendar_anchor, calendar_view),
        "offer_cards": offer_cards,
        "profile": get_profile(request.user),
        "weekday_labels": WEEKDAY_LABELS,
    }
    return render(request, "coop/dashboard.html", context)


def offer_detail(request, pk):
    offer = get_object_or_404(
        ProcurementOffer.objects.select_related("product", "source").prefetch_related("intents"),
        pk=pk,
    )
    can_write_intent = request.user.is_authenticated and request.user.is_active
    existing_intent = None
    if can_write_intent:
        existing_intent = MemberOfferIntent.objects.filter(member=request.user, offer=offer).first()

    if request.method == "POST":
        if not can_write_intent:
            return redirect_to_login(request.get_full_path(), None, REDIRECT_FIELD_NAME)
        if not offer.accepts_intents:
            messages.error(request, "Bu teklif artık üye talebi kabul etmiyor.")
            return redirect("offer_detail", pk=offer.pk)
        form = MemberOfferIntentForm(request.POST, instance=existing_intent)
        if form.is_valid():
            if _save_member_offer_intent(request, offer, form):
                messages.success(request, "Teklif talebiniz kaydedildi.")
                return redirect("offer_detail", pk=offer.pk)
    else:
        initial = {} if existing_intent else {"quantity": 1}
        form = MemberOfferIntentForm(instance=existing_intent, initial=initial)

    show_participation = can_write_intent
    intents = offer.intents.select_related("member", "delivery_point").order_by("-created_at") if show_participation else []
    payment_quantity = _payment_quantity_from_form(form, existing_intent)
    intent_payment_total = payment_quantity * offer.unit_price
    existing_intent_total = existing_intent.quantity * offer.unit_price if existing_intent else 0
    return render(
        request,
        "coop/offer_detail.html",
        {
            "offer": offer,
            "can_write_intent": can_write_intent,
            "form": form,
            "existing_intent": existing_intent,
            "existing_intent_total_display": _format_tl(existing_intent_total),
            "intent_payment_total_display": _format_tl(intent_payment_total),
            "intents": intents,
            "offer_progress_percent": _offer_progress_percent(offer),
            "show_participation": show_participation,
        },
    )


@login_required
@require_POST
def delete_offer_intent(request, pk):
    intent = get_object_or_404(MemberOfferIntent, pk=pk, member=request.user)
    offer_pk = intent.offer_id
    if not intent.offer.accepts_intents:
        messages.error(request, "Deadline geçtikten sonra talep iptal edilemez.")
        return redirect("offer_detail", pk=offer_pk)
    intent.delete()
    messages.success(request, "Teklif talebiniz iptal edildi.")
    return redirect("offer_detail", pk=offer_pk)
