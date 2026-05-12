from datetime import date, datetime
from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from solfasol.api_utils import DjangoValidationError, raise_bad_request, require_active_user

from .models import DeliveryPoint, MemberOfferIntent, ProcurementOffer, Product

router = Router(tags=["coop"])


class ProductOut(Schema):
    id: int
    name: str
    unit: str
    category: str
    reference_url: str


class DeliveryPointOut(Schema):
    id: int
    name: str
    address: str
    description: str


class SupplierSourceOut(Schema):
    id: int
    name: str
    website: str
    contact_info: str
    notes: str
    is_active: bool


class OfferIntentIn(Schema):
    quantity: int
    delivery_point_id: Optional[int] = None
    note: str = ""


class OfferIntentOut(Schema):
    id: int
    offer_id: int
    quantity: int
    delivery_point_id: Optional[int]
    note: str


class ProcurementOfferOut(Schema):
    id: int
    title: str
    product: ProductOut
    source: SupplierSourceOut
    unit_price: int
    target_quantity: int
    deadline: datetime
    fulfillment_date: Optional[date] = None
    discount_rate: Optional[int] = None
    status: str
    admin_note: str
    total_quantity: int
    remaining_quantity: int
    is_successful: bool
    accepts_intents: bool
    current_user_intent: Optional[OfferIntentOut] = None


def product_out(product):
    return ProductOut(
        id=product.id,
        name=product.name,
        unit=product.unit,
        category=product.category.name,
        reference_url=product.reference_url,
    )


def source_out(source):
    return SupplierSourceOut(
        id=source.id,
        name=source.name,
        website=source.website,
        contact_info=source.contact_info,
        notes=source.notes,
        is_active=source.is_active,
    )


def intent_out(intent):
    return OfferIntentOut(
        id=intent.id,
        offer_id=intent.offer_id,
        quantity=intent.quantity,
        delivery_point_id=intent.delivery_point_id,
        note=intent.note,
    )


def offer_out(request, offer):
    current_user_intent = None
    if request.user.is_authenticated:
        current_user_intent = next((intent for intent in offer.intents.all() if intent.member_id == request.user.id), None)
    return ProcurementOfferOut(
        id=offer.id,
        title=offer.display_title,
        product=product_out(offer.product),
        source=source_out(offer.source),
        unit_price=offer.unit_price,
        target_quantity=offer.target_quantity,
        deadline=offer.deadline,
        fulfillment_date=offer.fulfillment_date,
        discount_rate=offer.discount_rate,
        status=offer.status,
        admin_note=offer.admin_note,
        total_quantity=offer.total_quantity,
        remaining_quantity=offer.remaining_quantity,
        is_successful=offer.is_successful,
        accepts_intents=offer.accepts_intents,
        current_user_intent=intent_out(current_user_intent) if current_user_intent else None,
    )


def offer_queryset():
    return ProcurementOffer.objects.select_related("product", "product__category", "source").prefetch_related("intents")


@router.get("/catalog/products", response=list[ProductOut], auth=None)
def list_products(request):
    return [product_out(product) for product in Product.objects.filter(is_active=True).select_related("category")]


@router.get("/delivery-points", response=list[DeliveryPointOut], auth=None)
def list_delivery_points(request):
    return [
        DeliveryPointOut(id=point.id, name=point.name, address=point.address, description=point.description)
        for point in DeliveryPoint.objects.filter(is_active=True)
    ]


@router.get("/offers", response=list[ProcurementOfferOut], auth=None)
def list_offers(request):
    return [offer_out(request, offer) for offer in offer_queryset()]


@router.get("/offers/{offer_id}", response=ProcurementOfferOut, auth=None)
def get_offer(request, offer_id: int):
    offer = get_object_or_404(offer_queryset(), pk=offer_id)
    return offer_out(request, offer)


@router.post("/offers/{offer_id}/intent", response=OfferIntentOut)
def upsert_offer_intent(request, offer_id: int, payload: OfferIntentIn):
    require_active_user(request.user)
    offer = get_object_or_404(ProcurementOffer, pk=offer_id)
    delivery_point = None
    if payload.delivery_point_id:
        delivery_point = get_object_or_404(DeliveryPoint, pk=payload.delivery_point_id, is_active=True)
    intent = MemberOfferIntent.objects.filter(member=request.user, offer=offer).first()
    if intent is None:
        intent = MemberOfferIntent(member=request.user, offer=offer)
    intent.delivery_point = delivery_point
    intent.quantity = payload.quantity
    intent.note = payload.note
    try:
        intent.full_clean(validate_unique=False)
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    intent.save()
    return intent_out(intent)


@router.delete("/offer-intents/{intent_id}")
def delete_offer_intent(request, intent_id: int):
    require_active_user(request.user)
    intent = get_object_or_404(MemberOfferIntent.objects.select_related("offer"), pk=intent_id, member=request.user)
    if not intent.offer.accepts_intents:
        raise HttpError(400, "Deadline geçtikten sonra talep iptal edilemez.")
    intent.delete()
    return {"deleted": True}
