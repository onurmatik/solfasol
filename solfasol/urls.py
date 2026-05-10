"""
URL configuration for solfasol project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from coop import views as coop_views
from members import views as member_views
from solfasol.api import api

urlpatterns = [
    path('', coop_views.dashboard, name='dashboard'),
    path('offers/<int:pk>/', coop_views.offer_detail, name='offer_detail'),
    path('offer-intents/<int:pk>/delete/', coop_views.delete_offer_intent, name='delete_offer_intent'),
    path('invitations/', member_views.invitations, name='invitations'),
    path('invitations/<int:pk>/revoke/', member_views.revoke_invitation, name='revoke_invitation'),
    path('signup/<str:token>/', member_views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/v1/', api.urls),
    path('admin/', admin.site.urls),
]
