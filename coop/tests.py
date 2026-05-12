import json
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from calendar.models import CalendarEvent
from common.test_helpers import CoopFixtureMixin
from members.models import UserProfile

from .models import MemberOfferIntent, ProcurementOffer


class DashboardTests(CoopFixtureMixin, TestCase):
    def test_dashboard_is_public_and_renders_offers(self):
        CalendarEvent.objects.create(
            title="Kompost atölyesi",
            starts_at=timezone.now() + timedelta(days=1),
            status=CalendarEvent.Status.PUBLISHED,
        )
        MemberOfferIntent.objects.create(member=self.member, offer=self.offer, quantity=2)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Açık teklifler")
        self.assertContains(response, f'class="offer-sidebar-card" href="{reverse("offer_detail", kwargs={"pk": self.offer.pk})}"')
        self.assertContains(response, "5lt zeytinyağı · ABC Ziraat")
        self.assertContains(response, "Kazancın 30%")
        self.assertContains(response, "1000 TL / adet")
        self.assertNotContains(response, "Birim fiyat:")
        self.assertContains(response, "kaldı")
        self.assertContains(response, "Alınan sipariş")
        self.assertNotContains(response, "Ürün referansı")
        self.assertNotContains(response, "Tedarikçi URL")
        self.assertNotContains(response, "You save 30%")
        self.assertNotContains(response, "Sipariş ilerlemesi")
        self.assertNotContains(response, "Deadline:")
        self.assertNotContains(response, '<span class="badge info">Açık</span>', html=True)
        self.assertContains(response, "Aylık")
        self.assertContains(response, "Haftalık")
        self.assertContains(response, "weekly-calendar-grid")
        self.assertContains(response, "Yaklaşan etkinlikler")
        self.assertContains(response, "Kompost atölyesi")
        self.assertContains(response, "5lt zeytinyağı sipariş deadline")
        self.assertContains(response, "solfasol-logo.png")
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertNotContains(response, "Takvim etkinlikleri ve aktif sipariş talepleri tek ekranda.")
        self.assertNotContains(response, "Talep girmek için")
        self.assertNotContains(response, "Talebim var")

        self.client.login(username="member", password="pass12345")
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Talebim var")
        self.assertNotContains(response, "Talep gir")
        self.assertNotContains(response, "Talebi düzenle")
        self.assertNotContains(response, "Son taleplerim")

    def test_dashboard_weekly_view_uses_week_card_layout(self):
        self.client.login(username="member", password="pass12345")
        week_date = (timezone.localdate() + timedelta(days=3)).strftime("%Y-%m-%d")

        response = self.client.get(reverse("dashboard"), {"calendar_view": "week", "date": week_date})

        self.assertContains(response, "weekly-calendar-grid")
        self.assertContains(response, "weekly-day-card")
        self.assertContains(response, "Haftanın etkinlikleri")
        self.assertContains(response, "Deadline")
        self.assertContains(response, "5lt zeytinyağı sipariş deadline")


class ModelValidationTests(CoopFixtureMixin, TestCase):
    def test_offer_total_remaining_and_success_are_computed_from_intents(self):
        MemberOfferIntent.objects.create(member=self.member, offer=self.offer, quantity=4)
        other = User.objects.create_user(username="other")
        UserProfile.objects.create(user=other, is_coop_member=True)
        MemberOfferIntent.objects.create(member=other, offer=self.offer, quantity=6)

        self.assertEqual(self.offer.total_quantity, 10)
        self.assertEqual(self.offer.remaining_quantity, 0)
        self.assertTrue(self.offer.is_successful)

    def test_intent_rejects_deadline_passed_offer(self):
        expired_offer = ProcurementOffer.objects.create(
            title="Geçmiş teklif",
            product=self.product,
            source=self.source,
            unit_price=900,
            target_quantity=10,
            deadline=timezone.now() - timedelta(hours=1),
            fulfillment_date=date(2026, 5, 20),
        )
        intent = MemberOfferIntent(member=self.member, offer=expired_offer, quantity=1)

        with self.assertRaises(ValidationError):
            intent.full_clean()

    def test_intent_rejects_closed_offer(self):
        self.offer.status = ProcurementOffer.Status.CLOSED
        self.offer.save()
        intent = MemberOfferIntent(member=self.member, offer=self.offer, quantity=1)

        with self.assertRaises(ValidationError):
            intent.full_clean()

    def test_member_can_have_one_intent_per_offer(self):
        MemberOfferIntent.objects.create(member=self.member, offer=self.offer, quantity=1)
        duplicate = MemberOfferIntent(member=self.member, offer=self.offer, quantity=2)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_offer_fulfillment_date_is_optional(self):
        offer = ProcurementOffer(
            title="",
            product=self.product,
            source=self.source,
            unit_price=900,
            target_quantity=10,
            deadline=timezone.now() + timedelta(days=3),
            fulfillment_date=None,
        )

        offer.full_clean()

    def test_offer_rejects_fulfillment_date_before_deadline(self):
        deadline = timezone.now() + timedelta(days=3)
        offer = ProcurementOffer(
            title="",
            product=self.product,
            source=self.source,
            unit_price=900,
            target_quantity=10,
            deadline=deadline,
            fulfillment_date=timezone.localtime(deadline).date() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            offer.full_clean()


class CoopApiTests(CoopFixtureMixin, TestCase):
    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json")

    def patch_json(self, path, payload):
        return self.client.patch(path, data=json.dumps(payload), content_type="application/json")

    def test_offer_list_and_detail_include_target_progress(self):
        MemberOfferIntent.objects.create(member=self.member, offer=self.offer, quantity=3)

        response = self.client.get("/api/v1/offers")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload[0]["title"], "ABC Ziraat 5lt zeytinyağı")
        self.assertEqual(payload[0]["product"]["reference_url"], "https://example.com/product")
        self.assertEqual(payload[0]["discount_rate"], 30)
        self.assertEqual(payload[0]["unit_price"], 1000)
        self.assertEqual(payload[0]["target_quantity"], 10)
        self.assertEqual(payload[0]["total_quantity"], 3)
        self.assertIsNone(payload[0]["current_user_intent"])

        response = self.client.get(f"/api/v1/offers/{self.offer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["remaining_quantity"], 7)

        self.offer.fulfillment_date = None
        self.offer.save()
        response = self.client.get(f"/api/v1/offers/{self.offer.id}")
        self.assertEqual(response.json()["fulfillment_date"], None)

        self.client.login(username="member", password="pass12345")
        response = self.client.get("/api/v1/offers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["current_user_intent"]["quantity"], 3)

    def test_read_api_endpoints_are_public(self):
        self.assertEqual(self.client.get("/api/v1/catalog/products").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/delivery-points").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/offers").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/offers/{self.offer.id}").status_code, 200)

    def test_member_offer_intent_api_upserts_and_deletes(self):
        self.client.login(username="member", password="pass12345")

        response = self.post_json(
            f"/api/v1/offers/{self.offer.id}/intent",
            {"delivery_point_id": self.delivery_point.id, "quantity": 4, "note": "iki aile"},
        )

        self.assertEqual(response.status_code, 200, response.content)
        intent = MemberOfferIntent.objects.get(member=self.member, offer=self.offer)
        self.assertEqual(intent.quantity, 4)

        response = self.post_json(f"/api/v1/offers/{self.offer.id}/intent", {"quantity": 6})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(MemberOfferIntent.objects.count(), 1)
        intent.refresh_from_db()
        self.assertEqual(intent.quantity, 6)

        response = self.client.delete(f"/api/v1/offer-intents/{intent.id}")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(MemberOfferIntent.objects.count(), 0)

    def test_offer_intent_api_requires_login_but_not_member_profile(self):
        response = self.post_json(f"/api/v1/offers/{self.offer.id}/intent", {"quantity": "1"})

        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(MemberOfferIntent.objects.exists())

        user = User.objects.create_user(username="plain", password="pass12345")
        self.client.login(username="plain", password="pass12345")
        response = self.post_json(f"/api/v1/offers/{self.offer.id}/intent", {"quantity": "2"})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(MemberOfferIntent.objects.filter(member=user, offer=self.offer, quantity=2).exists())

    def test_deadline_blocks_intent_api_changes(self):
        self.offer.deadline = timezone.now() - timedelta(minutes=1)
        self.offer.save()
        self.client.login(username="member", password="pass12345")

        response = self.post_json(f"/api/v1/offers/{self.offer.id}/intent", {"quantity": "1"})

        self.assertEqual(response.status_code, 400)

    def test_admin_crud_api_routes_are_removed(self):
        self.client.login(username="staff", password="pass12345")

        self.assertEqual(self.post_json("/api/v1/admin/supplier-sources", {"name": "DEF Tarım"}).status_code, 404)
        self.assertEqual(self.patch_json(f"/api/v1/admin/supplier-sources/{self.source.id}", {"name": "Yeni"}).status_code, 404)
        self.assertEqual(
            self.post_json(
                "/api/v1/admin/offers",
                {
                    "title": "DEF nohut",
                    "product_id": self.product.id,
                    "source_id": self.source.id,
                    "unit_price": 250,
                    "target_quantity": 20,
                    "deadline": (timezone.now() + timedelta(days=2)).isoformat(),
                    "fulfillment_date": "2026-05-20",
                },
            ).status_code,
            404,
        )
        self.assertEqual(self.patch_json(f"/api/v1/admin/offers/{self.offer.id}", {"status": ProcurementOffer.Status.CLOSED}).status_code, 404)


class CoopViewTests(CoopFixtureMixin, TestCase):
    def test_dashboard_does_not_render_or_accept_intent_form(self):
        self.client.login(username="member", password="pass12345")

        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "Talep gir")
        self.assertNotContains(response, "Teslim noktası")
        self.assertNotContains(response, ">Not<")
        self.assertNotContains(response, "offer_intent")

        response = self.client.post(
            reverse("dashboard"),
            {
                "action": "offer_intent",
                "offer_id": self.offer.pk,
                "quantity": "2",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MemberOfferIntent.objects.exists())

    def test_supplier_offer_page_is_removed(self):
        self.client.login(username="member", password="pass12345")

        response = self.client.get("/supplier/offers/")

        self.assertEqual(response.status_code, 404)

    def test_offer_detail_allows_member_to_create_update_and_delete_intent(self):
        self.client.login(username="member", password="pass12345")

        response = self.client.post(
            reverse("offer_detail", kwargs={"pk": self.offer.pk}),
            {"quantity": "2", "delivery_point": self.delivery_point.id, "note": "deneme"},
        )
        self.assertRedirects(response, reverse("offer_detail", kwargs={"pk": self.offer.pk}))
        intent = MemberOfferIntent.objects.get(member=self.member, offer=self.offer)
        self.assertEqual(intent.quantity, 2)

        response = self.client.post(
            reverse("offer_detail", kwargs={"pk": self.offer.pk}),
            {"quantity": "3", "delivery_point": self.delivery_point.id},
        )
        self.assertRedirects(response, reverse("offer_detail", kwargs={"pk": self.offer.pk}))
        intent.refresh_from_db()
        self.assertEqual(intent.quantity, 3)

        response = self.client.post(reverse("delete_offer_intent", kwargs={"pk": intent.pk}))
        self.assertRedirects(response, reverse("offer_detail", kwargs={"pk": self.offer.pk}))
        self.assertFalse(MemberOfferIntent.objects.exists())

    def test_offer_detail_is_public_but_hides_participation_and_write_form(self):
        MemberOfferIntent.objects.create(
            member=self.member,
            offer=self.offer,
            quantity=2,
            delivery_point=self.delivery_point,
            note="özel not",
        )

        response = self.client.get(reverse("offer_detail", kwargs={"pk": self.offer.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ABC Ziraat 5lt zeytinyağı")
        self.assertContains(response, "https://example.com/product")
        self.assertContains(response, "You save 30%")
        self.assertContains(response, "Toplam")
        self.assertContains(response, "2")
        self.assertContains(response, "Katılım detayları için giriş yapın")
        self.assertContains(response, "Talep girmek için")
        self.assertNotContains(response, "member")
        self.assertNotContains(response, "özel not")
        self.assertNotContains(response, '<button class="primary" type="submit">Talep gir</button>', html=True)

    def test_anonymous_offer_detail_post_redirects_to_login(self):
        response = self.client.post(reverse("offer_detail", kwargs={"pk": self.offer.pk}), {"quantity": "2"})

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertFalse(MemberOfferIntent.objects.exists())

    def test_ops_routes_are_removed(self):
        self.client.login(username="staff", password="pass12345")

        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "Operasyon")

        response = self.client.get("/ops/")
        self.assertEqual(response.status_code, 404)

        response = self.client.post("/ops/", {"action": "source", "name": "GHI Kooperatif"})
        self.assertEqual(response.status_code, 404)

        response = self.client.post(f"/ops/offers/{self.offer.pk}/close/")
        self.assertEqual(response.status_code, 404)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, ProcurementOffer.Status.OPEN)
