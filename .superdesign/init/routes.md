# Routes

Source: `solfasol/urls.py`

| Route | Name | View | Template | Notes |
| --- | --- | --- | --- | --- |
| `/` | `dashboard` | `coop.views.dashboard` | `templates/coop/dashboard.html` | Landing page for authenticated users. |
| `/calendar/` | `calendar` | `calendar.views.agenda` | `templates/calendar/agenda.html` | Calendar agenda from manual events plus offer deadline/delivery entries. |
| `/offers/<int:pk>/` | `offer_detail` | `coop.views.offer_detail` | `templates/coop/offer_detail.html` | Offer details and member intent form. |
| `/offer-intents/<int:pk>/delete/` | `delete_offer_intent` | `coop.views.delete_offer_intent` | none | POST action. |
| `/invitations/` | `invitations` | `members.views.invitations` | `templates/members/invitations.html` | Invitation management. |
| `/signup/<str:token>/` | `signup` | `members.views.signup` | `templates/members/signup.html` | Invitation signup. |
| `/accounts/login/` | `login` | Django auth `LoginView` | `templates/registration/login.html` | Login. |

The requested change targets `/`, the landing page.
