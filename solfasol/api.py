from ninja import NinjaAPI
from ninja.security import django_auth

from calendar.api import router as calendar_router
from coop.api import router as coop_router
from members.api import router as members_router

api = NinjaAPI(title="Solfasol API", version="1.0.0", auth=django_auth)
api.add_router("", coop_router)
api.add_router("", members_router)
api.add_router("", calendar_router)
