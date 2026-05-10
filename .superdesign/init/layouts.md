# Layout Components

## Base Layout

Source: `templates/base.html`

The base layout is a compact operational shell:

- `html[lang=tr]`
- static stylesheet: `{% static 'css/solfasol.css' %}`
- `.app-shell` wraps the whole app.
- `.topbar` contains a constrained `.topbar-inner`.
- brand link points to `{% url 'dashboard' %}` with text `Solfasol`.
- navigation links: `Takvim`, authenticated `Teklifler`, `Davetler`, staff `Admin`, logout form, or guest `Giriş`.
- `.page` contains messages and page-specific `{% block content %}`.

## Layout CSS

Source: `static/css/solfasol.css`

- body background: `#f3f4f6`.
- page width: `min(1180px, calc(100% - 32px))`.
- topbar min height: `64px`.
- content top/bottom padding: `28px 0 48px`.
- panels/cards use white background, `1px` border, `8px` radius, subtle shadow.
- responsive breakpoint: `max-width: 760px`; topbar and page header stack, grids collapse to one column.
