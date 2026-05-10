from django.core.exceptions import ValidationError as DjangoValidationError
from ninja.errors import HttpError

from members.services import get_profile


def raise_bad_request(exc):
    if hasattr(exc, "message_dict"):
        detail = "; ".join(
            f"{field}: {', '.join(messages)}" for field, messages in exc.message_dict.items()
        )
        raise HttpError(400, detail)
    raise HttpError(400, str(exc))


def require_active_coop_member(user):
    profile = get_profile(user)
    if not user.is_authenticated or not user.is_active or profile is None or not profile.is_coop_member:
        raise HttpError(403, "Aktif üye hesabı gerekir.")


def require_staff(user):
    if not user.is_authenticated or not user.is_staff:
        raise HttpError(403, "Admin yetkisi gerekir.")


__all__ = ["DjangoValidationError", "raise_bad_request", "require_active_coop_member", "require_staff"]
