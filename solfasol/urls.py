from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.urls import path

from calendar import views as calendar_views
from coop import views as coop_views
from members.forms import EmailOrUsernameAuthenticationForm
from members import views as member_views
from solfasol.api import api

admin.site.site_header = "Solfasol Kooperatifi"
admin.site.site_title = "Solfasol Kooperatifi"
admin.site.index_title = "Solfasol Kooperatifi"

urlpatterns = [
    path('', coop_views.dashboard, name='dashboard'),
    path('calendar/', calendar_views.agenda, name='calendar'),
    path('offers/<int:pk>/', coop_views.offer_detail, name='offer_detail'),
    path('offer-intents/<int:pk>/delete/', coop_views.delete_offer_intent, name='delete_offer_intent'),
    path('signup/', member_views.signup, name='signup'),
    path('signup/complete/<uidb64>/<token>/', member_views.complete_signup, name='complete_signup'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='registration/auth.html',
            authentication_form=EmailOrUsernameAuthenticationForm,
            extra_context={"active_auth_tab": "login"},
        ),
        name='login',
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/v1/', api.urls),
    path(settings.ADMIN_URL_PATH, admin.site.urls),
]
