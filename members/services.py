from .models import UserProfile


def get_profile(user):
    if not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None
