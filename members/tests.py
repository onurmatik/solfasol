import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from common.test_helpers import CoopFixtureMixin

from .models import Invitation


class InvitationTests(CoopFixtureMixin, TestCase):
    def test_invitation_registers_active_coop_member_and_tracks_source(self):
        invitation = Invitation.objects.create(created_by=self.inviter, label="WhatsApp")

        response = self.client.post(
            reverse("signup", kwargs={"token": invitation.token}),
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
        self.assertTrue(user.profile.is_coop_member)
        self.assertEqual(user.profile.invited_by, self.inviter)
        self.assertEqual(user.profile.invitation, invitation)

    def test_revoked_invitation_cannot_register(self):
        invitation = Invitation.objects.create(created_by=self.inviter)
        invitation.revoke(self.inviter)

        response = self.client.get(reverse("signup", kwargs={"token": invitation.token}))

        self.assertEqual(response.status_code, 410)

    def test_member_can_create_and_revoke_own_invitation(self):
        self.client.login(username="member", password="pass12345")

        response = self.client.post(reverse("invitations"), {"label": "Facebook"})
        self.assertRedirects(response, reverse("invitations"))
        invitation = Invitation.objects.get(created_by=self.member, label="Facebook")

        response = self.client.post(reverse("revoke_invitation", kwargs={"pk": invitation.pk}))

        self.assertRedirects(response, reverse("invitations"))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.REVOKED)


class InvitationApiTests(CoopFixtureMixin, TestCase):
    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json")

    def test_invitation_api_requires_active_link_for_registration(self):
        invitation = Invitation.objects.create(created_by=self.inviter)

        response = self.post_json(
            "/api/v1/invitations/register",
            {"token": invitation.token, "username": "apiuser", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 200, response.content)
        user = User.objects.get(username="apiuser")
        self.assertEqual(user.profile.invited_by, self.inviter)
        self.assertTrue(user.profile.is_coop_member)

        invitation.revoke(self.inviter)
        response = self.post_json(
            "/api/v1/invitations/register",
            {"token": invitation.token, "username": "blocked", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 400)

    def test_member_can_list_own_invitations(self):
        Invitation.objects.create(created_by=self.member, label="Mahalle")
        Invitation.objects.create(created_by=self.inviter, label="Başka")
        self.client.login(username="member", password="pass12345")

        response = self.client.get("/api/v1/invitations")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["label"], "Mahalle")
