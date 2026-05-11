# Solfasol Design System

## Product Context
Solfasol is an Ankara-based, invitation-only online consumer cooperative. The first product surface is an operational web app for members and admins. Admins publish fixed procurement offers with a supplier/source, target quantity, deadline, price, and fulfillment date; members submit non-binding quantity intent until the deadline.

## Visual Direction
Adapt the Superdesign "Chrome Extension Landing Page" system-interface style into a Turkish cooperative operations tool. The UI should feel calm, practical, trustworthy, and data-dense without becoming a commercial marketplace.

## Fonts
- Primary: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif.
- Data labels: JetBrains Mono, "SFMono-Regular", Consolas, monospace.
- Do not use decorative, serif, or display fonts.

## Color Tokens
- Page background: #f3f4f6.
- Panel background: #ffffff.
- Soft panel: #f9fafb.
- Text: #111827.
- Muted text: #6b7280.
- Subtle text: #9ca3af.
- Border: #e5e7eb.
- Strong border: #d1d5db.
- Primary accent: #0891b2.
- Primary hover: #0e7490.
- Cooperative green: #15803d.
- Warning: #b45309.
- Danger: #b91c1c.
- Info tint: #ecfeff.
- Success tint: #f0fdf4.
- Warning tint: #fffbeb.
- Danger tint: #fef2f2.

## Layout
- Use a strict 4px/8px spacing grid.
- Brand/account navigation is a quiet page masthead, embedded inside the content width rather than a full-width top bar.
- Pages use constrained content width around 1180px with responsive single-column collapse.
- Use panels and tables for repeated operational information.
- Cards are limited to repeated entities and operational summaries, with max 8px radius.
- Avoid marketing hero sections, oversized decorative cards, gradients, bokeh/orbs, and stock imagery.

## Components
- Buttons: 8px radius, 1px border, clear icon/text affordances where icons exist, no oversized pill styling.
- Inputs: 8px radius, 1px border, 12px horizontal padding, visible labels.
- Tables: compact rows, muted headers, status badges, clear empty states.
- Status badges: small, uppercase-like visual density, mono-friendly labels when useful.
- Alerts: soft tint backgrounds with left border or concise text.

## Motion
Use minimal functional motion only: hover states, focus rings, and fast transitions under 160ms. No decorative scroll animations.

## Accessibility
High contrast text, visible focus states, form labels for every input, and no text overlapping controls. Turkish interface copy is the default.
