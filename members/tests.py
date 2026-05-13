import json

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from common.test_helpers import CoopFixtureMixin

from .models import UserProfile


class SignupTests(CoopFixtureMixin, TestCase):
    def completion_url(self, user, token=None):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token or default_token_generator.make_token(user)
        return reverse("complete_signup", args=[uid, token])

    def test_open_signup_creates_pending_user_profile_and_sends_completion_link(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "email": "new@example.com",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newmember")
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Solfasol kaydınızı tamamlayın")
        self.assertEqual(mail.outbox[0].from_email, "merhaba@solfasol.org")
        self.assertIn(self.completion_url(user), mail.outbox[0].body)
        self.assertIn("Solfasol hesabınız neredeyse hazır.", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        html_body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, "text/html")
        self.assertIn("Parolamı belirle", html_body)
        self.assertIn(self.completion_url(user), html_body)

    def test_pending_signup_resends_link_without_duplicate_user(self):
        payload = {"username": "newmember", "email": "new@example.com"}

        self.client.post(reverse("signup"), payload)
        response = self.client.post(reverse("signup"), payload)

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(User.objects.filter(username="newmember").count(), 1)
        self.assertEqual(UserProfile.objects.filter(user__username="newmember").count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_active_user_conflict_does_not_send_link(self):
        User.objects.create_user(username="newmember", password="pass12345", email="new@example.com")

        response = self.client.post(
            reverse("signup"),
            {"username": "newmember", "email": "new@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu kullanıcı adı zaten kullanılıyor.")
        self.assertContains(response, "Bu e-posta adresi zaten kullanılıyor.")
        self.assertEqual(len(mail.outbox), 0)

    def test_complete_signup_sets_password_activates_profile_and_logs_in(self):
        self.client.post(
            reverse("signup"),
            {"username": "newmember", "email": "new@example.com"},
        )
        user = User.objects.get(username="newmember")
        url = self.completion_url(user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Parolanızı belirleyin")

        response = self.client.post(url, {"new_password1": "short", "new_password2": "short"})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        response = self.client.post(
            url,
            {"new_password1": "complex-pass-123", "new_password2": "complex-pass-123"},
        )

        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("complex-pass-123"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_invalid_completion_link_is_rejected(self):
        self.client.post(
            reverse("signup"),
            {"username": "newmember", "email": "new@example.com"},
        )
        user = User.objects.get(username="newmember")

        response = self.client.get(self.completion_url(user, token="bad-token"))

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Bağlantı geçersiz", status_code=400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_signup_page_uses_shared_auth_tabs(self):
        response = self.client.get(reverse("signup"))

        self.assertContains(response, "auth-tabs")
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, f'href="{reverse("signup")}"')
        self.assertContains(response, "Kayıt ol")
        self.assertContains(response, "Giriş yap")
        self.assertContains(response, 'class="auth-tab active"')
        self.assertNotContains(response, "Ad soyad")

    def test_invitation_pages_are_removed(self):
        self.assertEqual(self.client.get("/invitations/").status_code, 404)
        self.assertEqual(self.client.get("/signup/legacy-token/").status_code, 404)


class LoginTests(TestCase):
    def test_login_page_uses_shared_auth_tabs(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "auth-tabs")
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, f'href="{reverse("signup")}"')
        self.assertContains(response, "Kayıt ol")
        self.assertContains(response, "Giriş yap")
        self.assertContains(response, 'class="auth-tab active"')

    def test_login_accepts_username_and_email(self):
        user = User.objects.create_user(username="member", password="pass12345", email="member@example.com")

        response = self.client.post(reverse("login"), {"username": "member", "password": "pass12345"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "member@example.com", "password": "pass12345"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_inactive_user_cannot_login(self):
        user = User(username="pending", email="pending@example.com", is_active=False)
        user.set_password("pass12345")
        user.save()

        response = self.client.post(reverse("login"), {"username": "pending", "password": "pass12345"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("login"), {"username": "pending@example.com", "password": "pass12345"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


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
