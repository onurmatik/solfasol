from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "status", "starts_at", "ends_at", "is_all_day", "location_name")
    list_filter = ("status", "event_type", "is_all_day", "starts_at")
    search_fields = ("title", "description", "location_name", "location_address", "link_url")
