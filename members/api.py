from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from .models import Invitation, UserProfile
from .services import can_create_invitations

router = Router(tags=["members"])


class InvitationIn(Schema):
    label: str = ""


class InvitationOut(Schema):
    id: int
    label: str
    token: str
    signup_url: str
    status: str
    accepted_count: int


class RegisterByInviteIn(Schema):
    token: str
    username: str
    password: str
    email: str = ""


class RegisterByInviteOut(Schema):
    id: int
    username: str


def invitation_out(request, invitation):
    return InvitationOut(
        id=invitation.id,
        label=invitation.label,
        token=invitation.token,
        signup_url=request.build_absolute_uri(invitation.get_signup_url()),
        status=invitation.status,
        accepted_count=getattr(invitation, "accepted_count", invitation.accepted_profiles.count()),
    )


@router.get("/invitations", response=list[InvitationOut])
def list_invitations(request):
    if not can_create_invitations(request.user):
        raise HttpError(403, "Davet linki için aktif üye gerekir.")
    queryset = Invitation.objects.annotate(accepted_count=Count("accepted_profiles"))
    if not request.user.is_staff:
        queryset = queryset.filter(created_by=request.user)
    return [invitation_out(request, invitation) for invitation in queryset]


@router.post("/invitations", response=InvitationOut)
def create_invitation(request, payload: InvitationIn):
    if not can_create_invitations(request.user):
        raise HttpError(403, "Davet linki için aktif üye gerekir.")
    invitation = Invitation.objects.create(created_by=request.user, label=payload.label)
    invitation.accepted_count = 0
    return invitation_out(request, invitation)


@router.post("/invitations/{invitation_id}/revoke", response=InvitationOut)
def revoke_invitation(request, invitation_id: int):
    invitation = get_object_or_404(Invitation, pk=invitation_id)
    if not (request.user.is_staff or invitation.created_by_id == request.user.id):
        raise HttpError(403, "Bu davet linkini iptal etme yetkiniz yok.")
    invitation.revoke(request.user)
    invitation.accepted_count = invitation.accepted_profiles.count()
    return invitation_out(request, invitation)


@router.post("/invitations/register", response=RegisterByInviteOut, auth=None)
def register_by_invite(request, payload: RegisterByInviteIn):
    invitation = get_object_or_404(Invitation, token=payload.token)
    if not invitation.is_usable:
        raise HttpError(400, "Davet linki artık geçerli değil.")
    with transaction.atomic():
        user = User.objects.create_user(username=payload.username, email=payload.email, password=payload.password)
        UserProfile.objects.create(
            user=user,
            is_coop_member=True,
            invited_by=invitation.created_by,
            invitation=invitation,
        )
    return RegisterByInviteOut(id=user.id, username=user.username)
