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
    location = models.CharField(max_length=255, blank=True, null=True)
    government_id = models.FileField(upload_to='donor/ids/', blank=True, null=True)

    def is_on_cooldown(self):
        if self.cooldown_until and timezone.now() < self.cooldown_until:
            return True
        return False

    def __str__(self):
        return f"{self.user.username} — {self.blood_type}"


class DonorApplication(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
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
    
class Notification(models.Model):
    NOTIF_TYPES = [
        ('approved', 'Application Approved'),
        ('rejected', 'Application Rejected'),
        ('request',  'Donation Request'),
        ('accepted', 'Request Accepted'),
        ('request_approved', 'Request Approved by Admin'),
        ('request_rejected', 'Request Rejected by Admin'),
    ]
    user       = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.CASCADE,
                     related_name='notifications'
                 )
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.notif_type}"