from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    is_coop_member = models.BooleanField(default=False, verbose_name="Kooperatif üyesi")
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
