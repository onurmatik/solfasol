from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvitationCreateForm, InvitationSignupForm
from .models import Invitation, UserProfile
from .services import can_create_invitations


def signup(request, token):
    invitation = get_object_or_404(Invitation, token=token)
    if not invitation.is_usable:
        return render(request, "members/signup_closed.html", {"invitation": invitation}, status=410)

    if request.method == "POST":
        form = InvitationSignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.email = form.cleaned_data.get("email", "")
                user.is_active = True
                user.save()
                UserProfile.objects.create(
                    user=user,
                    is_coop_member=True,
                    invited_by=invitation.created_by,
                    invitation=invitation,
                )
            login(request, user)
            messages.success(request, "Solfasol üyeliğiniz davet ile açıldı.")
            return redirect("dashboard")
    else:
        form = InvitationSignupForm()
    return render(request, "members/signup.html", {"form": form, "invitation": invitation})


@login_required
def invitations(request):
    if not can_create_invitations(request.user):
        messages.error(request, "Davet linki oluşturmak için aktif üye olmalısınız.")
        return redirect("dashboard")

    if request.method == "POST":
        form = InvitationCreateForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.created_by = request.user
            invitation.save()
            messages.success(request, "Davet linki oluşturuldu.")
            return redirect("invitations")
    else:
        form = InvitationCreateForm()

    queryset = Invitation.objects.filter(created_by=request.user).annotate(accepted_total=Count("accepted_profiles"))
    return render(request, "members/invitations.html", {"form": form, "invitations": queryset})


@login_required
@require_POST
def revoke_invitation(request, pk):
    invitation = get_object_or_404(Invitation, pk=pk)
    if not (request.user.is_staff or invitation.created_by_id == request.user.id):
        messages.error(request, "Bu davet linkini iptal etme yetkiniz yok.")
        return redirect("invitations")
    invitation.revoke(request.user)
    messages.success(request, "Davet linki iptal edildi.")
    return redirect("ops_dashboard" if request.user.is_staff and request.POST.get("next") == "ops" else "invitations")
