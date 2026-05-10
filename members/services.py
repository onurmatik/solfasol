from .models import UserProfile


def get_profile(user):
    if not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None


def can_create_invitations(user):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    profile = get_profile(user)
    return user.is_staff or (profile is not None and profile.is_coop_member)
