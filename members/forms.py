from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UsernameField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class SignupForm(forms.Form):
    username = forms.CharField(label="Kullanıcı adı", max_length=User._meta.get_field("username").max_length)
    email = forms.EmailField(label="E-posta")

    pending_user = None

    def clean_username(self):
        return self.cleaned_data["username"].strip()

    def clean_email(self):
        return User.objects.normalize_email(self.cleaned_data["email"]).strip()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if not username or not email:
            return cleaned_data

        username_user = User.objects.filter(username=username).first()
        email_users = list(User.objects.filter(email__iexact=email))

        if username_user:
            if username_user.is_active:
                self.add_error("username", "Bu kullanıcı adı zaten kullanılıyor.")
            elif username_user.has_usable_password() or username_user.email.lower() != email.lower():
                self.add_error("username", "Bu kullanıcı adıyla tamamlanmamış farklı bir kayıt var.")
            else:
                self.pending_user = username_user

        for email_user in email_users:
            if self.pending_user and email_user.pk == self.pending_user.pk:
                continue
            if email_user.is_active:
                self.add_error("email", "Bu e-posta adresi zaten kullanılıyor.")
            else:
                self.add_error("email", "Bu e-posta adresiyle tamamlanmamış farklı bir kayıt var.")

        if self.errors:
            return cleaned_data

        if self.pending_user:
            return cleaned_data

        user = User(username=username, email=email, is_active=False)
        user.set_unusable_password()
        try:
            user.full_clean()
        except ValidationError as exc:
            for field, errors in exc.message_dict.items():
                form_field = field if field in self.fields else None
                for error in errors:
                    self.add_error(form_field, error)
        return cleaned_data

    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]

        if self.pending_user:
            return self.pending_user

        user = User(username=username, email=email, is_active=False)
        user.set_unusable_password()
        user.save()
        return user


class CompleteSignupForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Parola"
        self.fields["new_password2"].label = "Parola (tekrar)"


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label="Kullanıcı adı veya e-posta",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
