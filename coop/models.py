from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from common.models import TimeStampedModel


class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ürün kategorisi"
        verbose_name_plural = "Ürün kategorileri"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    class Unit(models.TextChoices):
        KG = "kg", "kg"
        GR = "gr", "gr"
        LITER = "lt", "lt"
        PIECE = "adet", "adet"
        PACKAGE = "paket", "paket"

    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.KG)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]
        unique_together = [("category", "name")]
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class DeliveryPoint(TimeStampedModel):
    name = models.CharField(max_length=140, unique=True)
    address = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Teslim noktası"
        verbose_name_plural = "Teslim noktaları"

    def __str__(self):
        return self.name


class SupplierSource(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    website = models.URLField(blank=True)
    contact_info = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tedarikçi kaynağı"
        verbose_name_plural = "Tedarikçi kaynakları"

    def __str__(self):
        return self.name


class ProcurementOffer(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Açık"
        CLOSED = "closed", "Kapandı"

    title = models.CharField(max_length=160)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="procurement_offers")
    source = models.ForeignKey(SupplierSource, on_delete=models.PROTECT, related_name="procurement_offers")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    target_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    deadline = models.DateTimeField()
    fulfillment_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["deadline", "title"]
        verbose_name = "Teklif"
        verbose_name_plural = "Teklifler"

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.status == self.Status.OPEN

    @property
    def deadline_passed(self):
        return timezone.now() > self.deadline

    @property
    def accepts_intents(self):
        return self.is_open and not self.deadline_passed

    @property
    def total_quantity(self):
        total = self.intents.aggregate(total=Sum("quantity"))["total"]
        return total or Decimal("0")

    @property
    def remaining_quantity(self):
        remaining = self.target_quantity - self.total_quantity
        return max(remaining, Decimal("0"))

    @property
    def is_successful(self):
        return self.total_quantity >= self.target_quantity

    def clean(self):
        if self.product_id and not self.product.is_active:
            raise ValidationError("Pasif ürün için teklif verilemez.")
        if self.source_id and not self.source.is_active:
            raise ValidationError("Pasif tedarikçi kaynağı için teklif yayınlanamaz.")


class MemberOfferIntent(TimeStampedModel):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offer_intents")
    offer = models.ForeignKey(ProcurementOffer, on_delete=models.CASCADE, related_name="intents")
    delivery_point = models.ForeignKey(
        DeliveryPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offer_intents",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("member", "offer")]
        verbose_name = "Üye teklif talebi"
        verbose_name_plural = "Üye teklif talepleri"

    def __str__(self):
        return f"{self.member} - {self.offer} - {self.quantity}"

    def clean(self):
        if self.offer_id and not self.offer.accepts_intents:
            raise ValidationError("Bu teklif artık üye talebi kabul etmiyor.")
