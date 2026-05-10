from django.contrib import admin

from .models import (
    DeliveryPoint,
    MemberOfferIntent,
    ProcurementOffer,
    Product,
    ProductCategory,
    SupplierSource,
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "is_active")
    list_filter = ("category", "unit", "is_active")
    search_fields = ("name", "category__name")


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "address")


@admin.register(SupplierSource)
class SupplierSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "contact_info", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "website", "contact_info", "notes")


@admin.register(ProcurementOffer)
class ProcurementOfferAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "source",
        "unit_price",
        "target_quantity",
        "total_quantity",
        "status",
        "deadline",
        "fulfillment_date",
    )
    list_filter = ("status", "source", "product", "deadline", "fulfillment_date")
    search_fields = ("title", "product__name", "source__name", "admin_note")
    autocomplete_fields = ("product", "source")


@admin.register(MemberOfferIntent)
class MemberOfferIntentAdmin(admin.ModelAdmin):
    list_display = ("member", "offer", "quantity", "delivery_point", "created_at")
    list_filter = ("offer", "delivery_point", "created_at")
    search_fields = ("member__username", "member__email", "offer__title", "offer__product__name", "note")
    autocomplete_fields = ("member", "offer", "delivery_point")
