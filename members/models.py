import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from common.models import TimeStampedModel


def generate_invitation_token():
    return secrets.token_urlsafe(24)


class Invitation(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Aktif"
        REVOKED = "revoked", "İptal edildi"

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations")
    token = models.CharField(max_length=80, unique=True, default=generate_invitation_token)
    label = models.CharField(max_length=120, blank=True, help_text="WhatsApp, Facebook veya topluluk adı gibi kaynak etiketi.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_invitations",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Davet linki"
        verbose_name_plural = "Davet linkleri"

    def __str__(self):
        label = self.label or self.token[:8]
        return f"{label} - {self.created_by}"

    @property
    def is_usable(self):
        return self.status == self.Status.ACTIVE

    def revoke(self, user):
        self.status = self.Status.REVOKED
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.save(update_fields=["status", "revoked_at", "revoked_by", "updated_at"])

    def get_signup_url(self):
        return reverse("signup", kwargs={"token": self.token})


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    is_coop_member = models.BooleanField(default=False, verbose_name="Kooperatif üyesi")

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_members",
    )
    invitation = models.ForeignKey(
        Invitation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_profiles",
    )
    phone = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name = "Üye profili"
        verbose_name_plural = "Üye profilleri"

    def __str__(self):
        member_label = "koop üyesi" if self.is_coop_member else "üye"
        return f"{self.user.get_username()} ({member_label})"

    @property
    def is_active_coop_member(self):
        return self.user.is_active and self.is_coop_member
