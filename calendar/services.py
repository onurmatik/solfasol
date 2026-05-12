from dataclasses import dataclass
from datetime import datetime, time

from django.urls import reverse
from django.utils import timezone

from coop.models import ProcurementOffer

from .models import CalendarEvent


ORDER_DEADLINE = "order_deadline"
DELIVERY = "delivery"


EVENT_TYPE_LABELS = {
    ORDER_DEADLINE: "Sipariş deadline",
    DELIVERY: "Teslimat",
    CalendarEvent.EventType.EDUCATION: CalendarEvent.EventType.EDUCATION.label,
    CalendarEvent.EventType.COMMUNITY: CalendarEvent.EventType.COMMUNITY.label,
    CalendarEvent.EventType.EXTERNAL: CalendarEvent.EventType.EXTERNAL.label,
    CalendarEvent.EventType.OTHER: CalendarEvent.EventType.OTHER.label,
}


@dataclass(frozen=True)
class CalendarEntry:
    id: str
    source: str
    title: str
    event_type: str
    event_type_label: str
    starts_at: datetime
    ends_at: datetime | None
    is_all_day: bool
    description: str = ""
    location_name: str = ""
    location_address: str = ""
    link_url: str = ""
    offer_id: int | None = None

    @property
    def offer_url(self):
        if self.offer_id is None:
            return ""
        return reverse("offer_detail", kwargs={"pk": self.offer_id})


def _date_to_datetime(value):
    starts_at = datetime.combine(value, time.min)
    return timezone.make_aware(starts_at, timezone.get_current_timezone())


def _manual_entry(event):
    return CalendarEntry(
        id=f"event-{event.id}",
        source="manual",
        title=event.title,
        event_type=event.event_type,
        event_type_label=event.get_event_type_display(),
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        is_all_day=event.is_all_day,
        description=event.description,
        location_name=event.location_name,
        location_address=event.location_address,
        link_url=event.link_url,
    )


def _offer_entries(offer):
    title = offer.product.name
    entries = [
        CalendarEntry(
            id=f"offer-{offer.id}-deadline",
            source="offer",
            title=f"{title} sipariş deadline",
            event_type=ORDER_DEADLINE,
            event_type_label=EVENT_TYPE_LABELS[ORDER_DEADLINE],
            starts_at=offer.deadline,
            ends_at=None,
            is_all_day=False,
            offer_id=offer.id,
        ),
    ]
    if offer.fulfillment_date:
        entries.append(
            CalendarEntry(
                id=f"offer-{offer.id}-delivery",
                source="offer",
                title=f"{title} teslimat",
                event_type=DELIVERY,
                event_type_label=EVENT_TYPE_LABELS[DELIVERY],
                starts_at=_date_to_datetime(offer.fulfillment_date),
                ends_at=None,
                is_all_day=True,
                offer_id=offer.id,
            )
        )
    return entries


def list_calendar_entries():
    manual_entries = [
        _manual_entry(event)
        for event in CalendarEvent.objects.filter(status=CalendarEvent.Status.PUBLISHED).order_by("starts_at", "title")
    ]
    offer_entries = []
    offers = ProcurementOffer.objects.select_related("product").order_by("deadline", "title")
    for offer in offers:
        offer_entries.extend(_offer_entries(offer))
    return sorted([*manual_entries, *offer_entries], key=lambda entry: (entry.starts_at, entry.title))


def list_upcoming_calendar_entries(limit=None):
    today_start = timezone.make_aware(
        datetime.combine(timezone.localdate(), time.min),
        timezone.get_current_timezone(),
    )
    entries = [entry for entry in list_calendar_entries() if entry.starts_at >= today_start]
    if limit is None:
        return entries
    return entries[:limit]
