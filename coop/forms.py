from django import forms

from .models import MemberOfferIntent, SupplierSource


class MemberOfferIntentForm(forms.ModelForm):
    class Meta:
        model = MemberOfferIntent
        fields = ("quantity", "delivery_point", "note")
        labels = {
            "quantity": "Miktar",
            "delivery_point": "Teslim noktası",
            "note": "Not",
        }


class SupplierSourceForm(forms.ModelForm):
    class Meta:
        model = SupplierSource
        fields = ("name", "website", "contact_info", "notes", "is_active")
        labels = {
            "name": "Tedarikçi/kaynak adı",
            "website": "Web sitesi",
            "contact_info": "İletişim",
            "notes": "Not",
            "is_active": "Aktif",
        }
