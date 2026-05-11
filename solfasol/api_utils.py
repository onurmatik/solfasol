from django.core.exceptions import ValidationError as DjangoValidationError
from ninja.errors import HttpError


def raise_bad_request(exc):
    if hasattr(exc, "message_dict"):
        detail = "; ".join(
            f"{field}: {', '.join(messages)}" for field, messages in exc.message_dict.items()
        )
        raise HttpError(400, detail)
    raise HttpError(400, str(exc))


def require_active_user(user):
    if not user.is_authenticated or not user.is_active:
        raise HttpError(403, "Aktif hesap gerekir.")


__all__ = ["DjangoValidationError", "raise_bad_request", "require_active_user"]
