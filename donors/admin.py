from django.contrib import admin
from .models import DonorProfile, DonorApplication, DonationLog
admin.site.register(DonorProfile)
admin.site.register(DonorApplication)
admin.site.register(DonationLog)