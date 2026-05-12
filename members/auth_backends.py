from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = self._get_user_by_username(UserModel, username)
        if user is None:
            user = self._get_user_by_unique_active_email(UserModel, username)

        if user is None:
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _get_user_by_username(self, UserModel, username):
        try:
            return UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None

    def _get_user_by_unique_active_email(self, UserModel, email):
        users = list(UserModel._default_manager.filter(email__iexact=email, is_active=True)[:2])
        if len(users) == 1:
            return users[0]
        return None
