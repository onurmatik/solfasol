from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Invitation


class InvitationSignupForm(UserCreationForm):
    email = forms.EmailField(required=False, label="E-posta")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        labels = {"username": "Kullanıcı adı"}


class InvitationCreateForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ("label",)
        labels = {"label": "Kaynak etiketi"}
        help_texts = {"label": "Örn. WhatsApp mahalle grubu, Facebook duyurusu."}
