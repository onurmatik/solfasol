from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import CompleteSignupForm, SignupForm
from .models import UserProfile


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                UserProfile.objects.get_or_create(user=user)
            send_signup_completion_email(request, user)
            messages.success(request, "Hesabınızı tamamlamanız için e-posta adresinize bir bağlantı gönderdik.")
            return redirect("login")
    else:
        form = SignupForm()
    return render(request, "registration/auth.html", {"form": form, "active_auth_tab": "signup"})


def complete_signup(request, uidb64, token):
    user = get_signup_completion_user(uidb64, token)
    if user is None:
        return render(request, "members/complete_signup.html", {"invalid_link": True}, status=400)

    if request.method == "POST":
        form = CompleteSignupForm(user, request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                user.is_active = True
                user.save(update_fields=["is_active"])
                UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, "Solfasol hesabınız tamamlandı.")
            return redirect("dashboard")
    else:
        form = CompleteSignupForm(user)
    return render(request, "members/complete_signup.html", {"form": form})


def send_signup_completion_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    completion_url = request.build_absolute_uri(reverse("complete_signup", args=[uid, token]))
    context = {"completion_url": completion_url, "user": user}
    message = EmailMultiAlternatives(
        subject="Solfasol kaydınızı tamamlayın",
        body=render_to_string("members/emails/signup_completion.txt", context),
        to=[user.email],
    )
    message.attach_alternative(render_to_string("members/emails/signup_completion.html", context), "text/html")
    message.send()


def get_signup_completion_user(uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
        return None

    if user.is_active or user.has_usable_password():
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user
