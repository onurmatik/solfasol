from django import forms

from .models import MemberOfferIntent


class MemberOfferIntentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].widget.attrs.update({"min": "1", "step": "1"})
        self.fields["note"].widget.attrs["rows"] = 2

    class Meta:
        model = MemberOfferIntent
        fields = ("quantity", "delivery_point", "note")
        labels = {
            "quantity": "Miktar",
            "delivery_point": "Teslim noktası",
            "note": "Not",
        }
