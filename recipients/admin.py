from django.contrib import admin
from .models import BloodRequest
from .models import RecipientProfile

admin.site.register(BloodRequest)

@admin.register(RecipientProfile)
class RecipientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'blood_type', 'blood_type_locked']
    list_filter = ['blood_type', 'blood_type_locked']
    search_fields = ['user__username', 'user__email']