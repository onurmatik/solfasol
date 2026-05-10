from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from members.models import Invitation
from members.services import can_create_invitations, get_profile

from .forms import MemberOfferIntentForm, SupplierSourceForm
from .models import MemberOfferIntent, ProcurementOffer


@login_required
def dashboard(request):
    active_offers = (
        ProcurementOffer.objects.filter(status=ProcurementOffer.Status.OPEN)
        .select_related("product", "source")
        .prefetch_related("intents")
        .order_by("deadline")
    )
    my_intents = (
        MemberOfferIntent.objects.filter(member=request.user)
        .select_related("offer", "offer__product", "offer__source", "delivery_point")
        .order_by("-created_at")[:8]
    )
    context = {
        "active_offers": active_offers,
        "my_intents": my_intents,
        "profile": get_profile(request.user),
        "can_create_invitations": can_create_invitations(request.user),
    }
    return render(request, "coop/dashboard.html", context)


@login_required
def offer_detail(request, pk):
    offer = get_object_or_404(
        ProcurementOffer.objects.select_related("product", "source").prefetch_related("intents"),
        pk=pk,
    )
    existing_intent = MemberOfferIntent.objects.filter(member=request.user, offer=offer).first()

    if request.method == "POST":
        if not offer.accepts_intents:
            messages.error(request, "Bu teklif artık üye niyeti kabul etmiyor.")
            return redirect("offer_detail", pk=offer.pk)
        form = MemberOfferIntentForm(request.POST, instance=existing_intent)
        if form.is_valid():
            intent = form.save(commit=False)
            intent.member = request.user
            intent.offer = offer
            try:
                intent.full_clean(validate_unique=False)
            except Exception as exc:
                form.add_error(None, exc)
            else:
                MemberOfferIntent.objects.update_or_create(
                    member=request.user,
                    offer=offer,
                    defaults={
                        "quantity": intent.quantity,
                        "delivery_point": intent.delivery_point,
                        "note": intent.note,
                    },
                )
                messages.success(request, "Teklif niyetiniz kaydedildi.")
                return redirect("offer_detail", pk=offer.pk)
    else:
        form = MemberOfferIntentForm(instance=existing_intent)

    intents = offer.intents.select_related("member", "delivery_point").order_by("-created_at")
    return render(
        request,
        "coop/offer_detail.html",
        {
            "offer": offer,
            "form": form,
            "existing_intent": existing_intent,
            "intents": intents,
        },
    )


@login_required
@require_POST
def delete_offer_intent(request, pk):
    intent = get_object_or_404(MemberOfferIntent, pk=pk, member=request.user)
    offer_pk = intent.offer_id
    if not intent.offer.accepts_intents:
        messages.error(request, "Deadline geçtikten sonra niyet iptal edilemez.")
        return redirect("offer_detail", pk=offer_pk)
    intent.delete()
    messages.success(request, "Teklif niyetiniz iptal edildi.")
    return redirect("offer_detail", pk=offer_pk)


@staff_member_required
def ops_dashboard(request):
    source_form = SupplierSourceForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "source":
            source_form = SupplierSourceForm(request.POST)
            if source_form.is_valid():
                source_form.save()
                messages.success(request, "Tedarikçi kaynağı oluşturuldu.")
                return redirect("ops_dashboard")

    offers = ProcurementOffer.objects.select_related("product", "source").prefetch_related("intents")[:25]
    intents = MemberOfferIntent.objects.select_related("member", "offer", "offer__product", "delivery_point")[:25]
    invitations = Invitation.objects.select_related("created_by", "revoked_by").annotate(accepted_total=Count("accepted_profiles"))[:25]
    return render(
        request,
        "coop/ops_dashboard.html",
        {
            "source_form": source_form,
            "offers": offers,
            "intents": intents,
            "invitations": invitations,
        },
    )


@staff_member_required
@require_POST
def close_offer(request, pk):
    offer = get_object_or_404(ProcurementOffer, pk=pk)
    offer.status = ProcurementOffer.Status.CLOSED
    offer.save(update_fields=["status", "updated_at"])
    messages.success(request, "Teklif kapatıldı.")
    return redirect("ops_dashboard")
