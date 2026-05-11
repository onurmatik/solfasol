import calendar as python_calendar
import json
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from common.test_helpers import CoopFixtureMixin

from .models import CalendarEvent


class CalendarModelTests(TestCase):
    def test_end_time_must_be_after_start_time(self):
        starts_at = timezone.now()
        event = CalendarEvent(
            title="Atölye",
            starts_at=starts_at,
            ends_at=starts_at - timedelta(minutes=1),
            status=CalendarEvent.Status.PUBLISHED,
        )

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_calendar_app_keeps_stdlib_calendar_functions_available(self):
        self.assertEqual(python_calendar.monthrange(2026, 5), (4, 31))
        self.assertTrue(callable(python_calendar.timegm))


class CalendarViewTests(CoopFixtureMixin, TestCase):
    def test_public_agenda_lists_published_manual_and_offer_events(self):
        CalendarEvent.objects.create(
            title="Kompost atölyesi",
            description="Community center buluşması",
            event_type=CalendarEvent.EventType.EDUCATION,
            starts_at=timezone.now() + timedelta(days=1),
            location_name="Community Center",
            status=CalendarEvent.Status.PUBLISHED,
        )
        CalendarEvent.objects.create(
            title="Taslak etkinlik",
            starts_at=timezone.now() + timedelta(days=2),
            status=CalendarEvent.Status.DRAFT,
        )
        CalendarEvent.objects.create(
            title="İptal etkinlik",
            starts_at=timezone.now() + timedelta(days=3),
            status=CalendarEvent.Status.CANCELED,
        )

        response = self.client.get(reverse("calendar"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kompost atölyesi")
        self.assertContains(response, "Community Center")
        self.assertContains(response, "5lt zeytinyağı sipariş deadline")
        self.assertContains(response, "5lt zeytinyağı teslimat")
        self.assertNotContains(response, "Taslak etkinlik")
        self.assertNotContains(response, "İptal etkinlik")
        self.assertNotContains(response, "1000.00 TL")
        self.assertNotContains(response, "ABC Ziraat")
        self.assertNotContains(response, "Toplam / hedef")

    def test_public_visitor_can_open_offer_from_calendar(self):
        response = self.client.get(reverse("calendar"))

        self.assertContains(response, reverse("offer_detail", kwargs={"pk": self.offer.pk}))


class CalendarApiTests(CoopFixtureMixin, TestCase):
    def test_public_calendar_api_returns_summary_and_offer_links(self):
        CalendarEvent.objects.create(
            title="Forum",
            event_type=CalendarEvent.EventType.COMMUNITY,
            starts_at=timezone.now() + timedelta(days=1),
            status=CalendarEvent.Status.PUBLISHED,
        )

        response = self.client.get("/api/v1/calendar")

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        offer_entries = [entry for entry in payload if entry["source"] == "offer"]
        self.assertEqual(len(offer_entries), 2)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertIn("Forum", serialized)
        self.assertIn("5lt zeytinyağı sipariş deadline", serialized)
        self.assertNotIn("1000.00", serialized)
        self.assertNotIn("ABC Ziraat", serialized)
        self.assertTrue(all(entry["offer_url"] == reverse("offer_detail", kwargs={"pk": self.offer.pk}) for entry in offer_entries))
