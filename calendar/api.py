from datetime import datetime
from typing import Optional

from ninja import Router, Schema

from .services import list_calendar_entries

router = Router(tags=["calendar"])


class CalendarEntryOut(Schema):
    id: str
    source: str
    title: str
    event_type: str
    event_type_label: str
    starts_at: datetime
    ends_at: Optional[datetime]
    is_all_day: bool
    description: str
    location_name: str
    location_address: str
    link_url: str
    offer_url: str = ""


def entry_out(request, entry):
    offer_url = ""
    if entry.offer_id and request.user.is_authenticated:
        offer_url = entry.offer_url
    return CalendarEntryOut(
        id=entry.id,
        source=entry.source,
        title=entry.title,
        event_type=entry.event_type,
        event_type_label=entry.event_type_label,
        starts_at=entry.starts_at,
        ends_at=entry.ends_at,
        is_all_day=entry.is_all_day,
        description=entry.description,
        location_name=entry.location_name,
        location_address=entry.location_address,
        link_url=entry.link_url,
        offer_url=offer_url,
    )


@router.get("/calendar", response=list[CalendarEntryOut], auth=None)
def list_calendar(request):
    return [entry_out(request, entry) for entry in list_calendar_entries()]
