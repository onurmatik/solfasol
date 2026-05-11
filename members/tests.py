import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from common.test_helpers import CoopFixtureMixin

from .models import UserProfile


class SignupTests(CoopFixtureMixin, TestCase):
    def test_open_signup_creates_active_user_profile_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "email": "new@example.com",
                "password1": "complex-pass-123",
                "password2": "complex-pass-123",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="newmember")
        self.assertTrue(user.is_active)
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_invitation_pages_are_removed(self):
        self.assertEqual(self.client.get("/invitations/").status_code, 404)
        self.assertEqual(self.client.get("/signup/legacy-token/").status_code, 404)


class RegistrationApiTests(CoopFixtureMixin, TestCase):
    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json")

    def test_register_api_creates_active_user_profile(self):
        response = self.post_json(
            "/api/v1/register",
            {"username": "apiuser", "password": "pass12345", "email": "api@example.com"},
        )

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        user = User.objects.get(username="apiuser")
        self.assertEqual(payload, {"id": user.id, "username": "apiuser"})
        self.assertTrue(user.is_active)
        self.assertEqual(user.email, "api@example.com")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_invitation_api_routes_are_removed(self):
        self.assertEqual(self.client.get("/api/v1/invitations").status_code, 404)
        self.assertEqual(
            self.post_json("/api/v1/invitations/register", {"token": "x", "username": "u", "password": "pass12345"}).status_code,
            404,
        )
        self.assertEqual(self.post_json("/api/v1/invitations/1/revoke", {}).status_code, 404)
