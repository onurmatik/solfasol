# Components Inventory

Solfasol uses Django templates with shared CSS classes from `static/css/solfasol.css`.

## Shared Primitives

- `.brand-row`, `.brand`, `.brand-logo`, `.account-actions`, `.user-avatar`: quiet page masthead in `templates/base.html`.
- `.page`: centered main content wrapper, max width 1180px.
- `.page-header`: page title/action header.
- `.panel`: primary surface for page sections.
- `.card`: repeated entity card, used for offers.
- `.grid.two`, `.grid.three`: responsive grid layouts.
- `.stack`: vertical rhythm helper.
- `.row`, `.row.between`: inline alignment helpers.
- `.button`, `.button.primary`, `.button.danger`, `.button.linklike`: action controls.
- `.badge`, `.badge.success`, `.badge.warning`, `.badge.danger`: status indicators.
- `.stat`: metric label/value block.
- `.table-wrap`, `table`, `th`, `td`: compact tabular data.
- `.empty`: dashed empty state.
- `.message`, `.messages`: notices.
- `.agenda-list`, `.agenda-item`, `.agenda-date`: calendar agenda preview/list UI.

## Icons And Assets

The brand uses `static/img/solfasol-logo.png` with the subtitle `Kooperatifi`.

## Current Landing Page Components

`templates/coop/dashboard.html` extends `templates/base.html` and uses:

- page header with member panel eyebrow, H1, helper copy, optional invitation link.
- 7/5 dashboard grid: left/main column for calendar, right sidebar for active order requests.
- calendar panel with month/week segmented toggle, previous/next period controls, compact seven-column calendar grid, day markers, and current-day highlight.
- upcoming events panel below calendar, rendered as repeated event list rows with date boxes and event badges.
- active offer sidebar cards include title, source/product metadata, status badge, progress, delivery/deadline metadata, and a `Talebim var` intent badge when the current user has an intent.
- the separate "Son taleplerim" table is intentionally not used on the landing page.

## Calendar Page Components

`templates/calendar/agenda.html` extends `templates/base.html` and uses:

- page header with calendar copy.
- single `.panel` containing `.agenda-list`.
- repeated `.agenda-item` with date/time column, title, event type metadata, badge, optional description, location, and link.
