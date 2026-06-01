from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_flagged', 'flag_count', 'flagged_until']
    list_filter = ['is_flagged', 'role']
    fieldsets = UserAdmin.fieldsets + (
        ('Flag Info', {
            'fields': ('is_flagged', 'flag_count', 'flagged_until')
        }),
    )
