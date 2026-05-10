from django.contrib import admin

from .models import Invitation, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_coop_member", "invited_by", "invitation", "created_at")
    list_filter = ("is_coop_member", "created_at")
    search_fields = ("user__username", "user__email", "phone", "invited_by__username", "invitation__label")
    autocomplete_fields = ("user", "invited_by", "invitation")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("label", "created_by", "status", "accepted_count", "created_at", "revoked_at")
    list_filter = ("status", "created_at")
    search_fields = ("label", "token", "created_by__username", "created_by__email")
    readonly_fields = ("token", "created_at", "updated_at", "revoked_at", "revoked_by")
    autocomplete_fields = ("created_by",)

    @admin.display(description="Kayıt")
    def accepted_count(self, obj):
        return obj.accepted_profiles.count()
