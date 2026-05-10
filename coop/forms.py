from django import forms

from .models import MemberOfferIntent


class MemberOfferIntentForm(forms.ModelForm):
    class Meta:
        model = MemberOfferIntent
        fields = ("quantity", "delivery_point", "note")
        labels = {
            "quantity": "Miktar",
            "delivery_point": "Teslim noktası",
            "note": "Not",
        }
