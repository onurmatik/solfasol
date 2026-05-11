from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_coop_member", "created_at")
    list_filter = ("is_coop_member", "created_at")
    search_fields = ("user__username", "user__email", "phone")
    autocomplete_fields = ("user",)
