# Page Dependency Trees

## Landing Page (`/`)

- `solfasol/urls.py`
  - `coop.views.dashboard`
    - `ProcurementOffer` active open offers
    - `MemberOfferIntent` current-user intents matched to active offers for inline badges
    - calendar entries for month/week grid and upcoming event list
    - `members.services.get_profile`
    - `members.services.can_create_invitations`
  - renders `templates/coop/dashboard.html`
    - extends `templates/base.html`
    - stylesheet `static/css/solfasol.css`

Visual dependencies:

- `templates/base.html`
- `templates/coop/dashboard.html`
- `static/css/solfasol.css`
- `.superdesign/design-system.md`

## Calendar Page (`/calendar/`)

- `solfasol/urls.py`
  - `calendar.views.agenda`
    - `calendar.services.list_calendar_entries`
      - `CalendarEvent`
      - `ProcurementOffer`
  - renders `templates/calendar/agenda.html`
    - extends `templates/base.html`
    - stylesheet `static/css/solfasol.css`

Visual dependencies:

- `templates/base.html`
- `templates/calendar/agenda.html`
- `static/css/solfasol.css`
- `.superdesign/design-system.md`

## Offer Detail (`/offers/<id>/`)

- `coop.views.offer_detail`
  - `MemberOfferIntentForm`
  - `ProcurementOffer`
  - `MemberOfferIntent`
  - renders `templates/coop/offer_detail.html`
    - extends `templates/base.html`
    - stylesheet `static/css/solfasol.css`

Visual dependencies:

- `templates/base.html`
- `templates/coop/offer_detail.html`
- `static/css/solfasol.css`
- `.superdesign/design-system.md`
