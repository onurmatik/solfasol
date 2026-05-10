from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from members.services import can_create_invitations, get_profile

from .forms import MemberOfferIntentForm
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
            messages.error(request, "Bu teklif artık üye talebi kabul etmiyor.")
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
                messages.success(request, "Teklif talebiniz kaydedildi.")
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
        messages.error(request, "Deadline geçtikten sonra talep iptal edilemez.")
        return redirect("offer_detail", pk=offer_pk)
    intent.delete()
    messages.success(request, "Teklif talebiniz iptal edildi.")
    return redirect("offer_detail", pk=offer_pk)
