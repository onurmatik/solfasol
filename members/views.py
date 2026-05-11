from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import SignupForm
from .models import UserProfile


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data.get("email", "")
                user.is_active = True
                user.save()
                UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Solfasol hesabınız oluşturuldu.")
            return redirect("dashboard")
    else:
        form = SignupForm()
    return render(request, "members/signup.html", {"form": form})
