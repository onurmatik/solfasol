from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from ninja import Router, Schema

from solfasol.api_utils import raise_bad_request

from .models import UserProfile

router = Router(tags=["members"])


class RegisterIn(Schema):
    username: str
    password: str
    email: str = ""


class RegisterOut(Schema):
    id: int
    username: str


@router.post("/register", response=RegisterOut, auth=None)
def register(request, payload: RegisterIn):
    try:
        validate_password(payload.password)
    except ValidationError as exc:
        raise_bad_request(exc)

    with transaction.atomic():
        user = User(username=payload.username, email=User.objects.normalize_email(payload.email))
        user.set_password(payload.password)
        try:
            user.full_clean()
        except ValidationError as exc:
            raise_bad_request(exc)
        user.save()
        UserProfile.objects.create(user=user)
    return RegisterOut(id=user.id, username=user.username)
