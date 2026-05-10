from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from solfasol.api_utils import DjangoValidationError, raise_bad_request, require_active_coop_member, require_staff

from .models import DeliveryPoint, MemberOfferIntent, ProcurementOffer, Product, SupplierSource

router = Router(tags=["coop"])


class ProductOut(Schema):
    id: int
    name: str
    unit: str
    category: str


class DeliveryPointOut(Schema):
    id: int
    name: str
    address: str
    description: str


class SupplierSourceIn(Schema):
    name: str
    website: str = ""
    contact_info: str = ""
    notes: str = ""
    is_active: bool = True


class SupplierSourcePatch(Schema):
    name: Optional[str] = None
    website: Optional[str] = None
    contact_info: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierSourceOut(Schema):
    id: int
    name: str
    website: str
    contact_info: str
    notes: str
    is_active: bool


class OfferIntentIn(Schema):
    quantity: Decimal
    delivery_point_id: Optional[int] = None
    note: str = ""


class OfferIntentOut(Schema):
    id: int
    offer_id: int
    quantity: Decimal
    delivery_point_id: Optional[int]
    note: str


class ProcurementOfferIn(Schema):
    title: str
    product_id: int
    source_id: int
    unit_price: Decimal
    target_quantity: Decimal
    deadline: datetime
    fulfillment_date: date
    status: str = ProcurementOffer.Status.OPEN
    admin_note: str = ""


class ProcurementOfferPatch(Schema):
    title: Optional[str] = None
    product_id: Optional[int] = None
    source_id: Optional[int] = None
    unit_price: Optional[Decimal] = None
    target_quantity: Optional[Decimal] = None
    deadline: Optional[datetime] = None
    fulfillment_date: Optional[date] = None
    status: Optional[str] = None
    admin_note: Optional[str] = None


class ProcurementOfferOut(Schema):
    id: int
    title: str
    product: ProductOut
    source: SupplierSourceOut
    unit_price: Decimal
    target_quantity: Decimal
    deadline: datetime
    fulfillment_date: date
    status: str
    admin_note: str
    total_quantity: Decimal
    remaining_quantity: Decimal
    is_successful: bool
    accepts_intents: bool
    current_user_intent: Optional[OfferIntentOut] = None


def product_out(product):
    return ProductOut(id=product.id, name=product.name, unit=product.unit, category=product.category.name)


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
        title=offer.title,
        product=product_out(offer.product),
        source=source_out(offer.source),
        unit_price=offer.unit_price,
        target_quantity=offer.target_quantity,
        deadline=offer.deadline,
        fulfillment_date=offer.fulfillment_date,
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


@router.get("/catalog/products", response=list[ProductOut])
def list_products(request):
    return [product_out(product) for product in Product.objects.filter(is_active=True).select_related("category")]


@router.get("/delivery-points", response=list[DeliveryPointOut])
def list_delivery_points(request):
    return [
        DeliveryPointOut(id=point.id, name=point.name, address=point.address, description=point.description)
        for point in DeliveryPoint.objects.filter(is_active=True)
    ]


@router.get("/offers", response=list[ProcurementOfferOut])
def list_offers(request):
    return [offer_out(request, offer) for offer in offer_queryset()]


@router.get("/offers/{offer_id}", response=ProcurementOfferOut)
def get_offer(request, offer_id: int):
    offer = get_object_or_404(offer_queryset(), pk=offer_id)
    return offer_out(request, offer)


@router.post("/offers/{offer_id}/intent", response=OfferIntentOut)
def upsert_offer_intent(request, offer_id: int, payload: OfferIntentIn):
    require_active_coop_member(request.user)
    offer = get_object_or_404(ProcurementOffer, pk=offer_id)
    delivery_point = None
    if payload.delivery_point_id:
        delivery_point = get_object_or_404(DeliveryPoint, pk=payload.delivery_point_id, is_active=True)
    intent = MemberOfferIntent(
        member=request.user,
        offer=offer,
        delivery_point=delivery_point,
        quantity=payload.quantity,
        note=payload.note,
    )
    try:
        intent.full_clean(validate_unique=False)
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    intent, _created = MemberOfferIntent.objects.update_or_create(
        member=request.user,
        offer=offer,
        defaults={"delivery_point": delivery_point, "quantity": payload.quantity, "note": payload.note},
    )
    return intent_out(intent)


@router.delete("/offer-intents/{intent_id}")
def delete_offer_intent(request, intent_id: int):
    require_active_coop_member(request.user)
    intent = get_object_or_404(MemberOfferIntent.objects.select_related("offer"), pk=intent_id, member=request.user)
    if not intent.offer.accepts_intents:
        raise HttpError(400, "Deadline geçtikten sonra niyet iptal edilemez.")
    intent.delete()
    return {"deleted": True}


@router.post("/admin/supplier-sources", response=SupplierSourceOut)
def admin_create_supplier_source(request, payload: SupplierSourceIn):
    require_staff(request.user)
    source = SupplierSource(**payload.dict())
    try:
        source.full_clean()
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    source.save()
    return source_out(source)


@router.patch("/admin/supplier-sources/{source_id}", response=SupplierSourceOut)
def admin_update_supplier_source(request, source_id: int, payload: SupplierSourcePatch):
    require_staff(request.user)
    source = get_object_or_404(SupplierSource, pk=source_id)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(source, field, value)
    try:
        source.full_clean()
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    source.save()
    return source_out(source)


@router.post("/admin/offers", response=ProcurementOfferOut)
def admin_create_offer(request, payload: ProcurementOfferIn):
    require_staff(request.user)
    product = get_object_or_404(Product, pk=payload.product_id)
    source = get_object_or_404(SupplierSource, pk=payload.source_id)
    offer = ProcurementOffer(
        title=payload.title,
        product=product,
        source=source,
        unit_price=payload.unit_price,
        target_quantity=payload.target_quantity,
        deadline=payload.deadline,
        fulfillment_date=payload.fulfillment_date,
        status=payload.status,
        admin_note=payload.admin_note,
    )
    try:
        offer.full_clean()
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    offer.save()
    return offer_out(request, offer_queryset().get(pk=offer.pk))


@router.patch("/admin/offers/{offer_id}", response=ProcurementOfferOut)
def admin_update_offer(request, offer_id: int, payload: ProcurementOfferPatch):
    require_staff(request.user)
    offer = get_object_or_404(ProcurementOffer, pk=offer_id)
    data = payload.dict(exclude_unset=True)
    if "product_id" in data:
        offer.product = get_object_or_404(Product, pk=data.pop("product_id"))
    if "source_id" in data:
        offer.source = get_object_or_404(SupplierSource, pk=data.pop("source_id"))
    for field, value in data.items():
        setattr(offer, field, value)
    try:
        offer.full_clean()
    except DjangoValidationError as exc:
        raise_bad_request(exc)
    offer.save()
    return offer_out(request, offer_queryset().get(pk=offer.pk))
