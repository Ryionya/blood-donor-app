from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

BLOOD_TYPE_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]

class DonorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donor_profile')
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    cooldown_until = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(blank=True)

    def is_on_cooldown(self):
        if self.cooldown_until and timezone.now() < self.cooldown_until:
            return True
        return False

    def __str__(self):
        return f"{self.user.username} — {self.blood_type}"


class DonorApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    donor = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application')
    government_id = models.FileField(upload_to='applications/ids/')
    medical_certificate = models.FileField(upload_to='applications/certs/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.donor.username} — {self.status}"


class DonationLog(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donation_logs')
    donated_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-set cooldown on the donor's profile
        profile = self.donor.donor_profile
        profile.cooldown_until = self.donated_at + timedelta(days=56)
        profile.is_available = False
        profile.save()

    def __str__(self):
        return f"{self.donor.username} donated on {self.donated_at.date()}"