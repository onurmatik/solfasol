# Layout Components

## Base Layout

Source: `templates/base.html`

The base layout is a compact operational shell:

- `html[lang=tr]`
- static stylesheet: `{% static 'css/solfasol.css' %}`
- `.app-shell` wraps the whole app.
- `.page` contains a quiet `.brand-row`, messages, and page-specific `{% block content %}`.
- brand link points to `{% url 'dashboard' %}` and displays `static/img/solfasol-logo.png`.
- `.account-actions` shows either a user avatar or guest `login` action.

## Layout CSS

Source: `static/css/solfasol.css`

- body background: `#f3f4f6`.
- page width: `min(1180px, calc(100% - 32px))`.
- masthead sits inside the page content width with no full-width header band, border, or shadow.
- content top/bottom padding: `28px 0 48px`.
- panels/cards use white background, `1px` border, `8px` radius, subtle shadow.
- responsive breakpoint: `max-width: 760px`; masthead stays as a compact brand/account row, page header stacks, grids collapse to one column.
