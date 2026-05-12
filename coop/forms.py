from django import forms

from .models import MemberOfferIntent


class MemberOfferIntentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].widget.attrs.update(
            {
                "min": "1",
                "step": "1",
                "data-payment-quantity": "true",
            }
        )
        self.fields["note"].widget.attrs.update(
            {
                "rows": 2,
                "placeholder": "Teslimat veya ürün tercihiyle ilgili notunuz...",
            }
        )

    class Meta:
        model = MemberOfferIntent
        fields = ("quantity", "delivery_point", "note")
        labels = {
            "quantity": "Miktar",
            "delivery_point": "Teslim noktası",
            "note": "Not",
        }
