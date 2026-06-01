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
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPE_CHOICES, blank=True)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_blood_type_locked = models.BooleanField(default=False)
    cooldown_until = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    government_id = models.FileField(upload_to='donor/ids/', blank=True, null=True)
    blood_type_locked = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_expires_at = models.DateTimeField(null=True, blank=True)

    def is_on_cooldown(self):
        if self.cooldown_until and timezone.now() < self.cooldown_until:
            return True
        return False

    def is_verification_expired(self):
        if self.verification_expires_at and timezone.now() >= self.verification_expires_at:
            return True
        return False

    def __str__(self):
        return f"{self.user.username} — {self.blood_type}"


class DonorApplication(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_UNVERIFIED = "unverified"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_UNVERIFIED, "Unverified"),
    ]
    
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    medical_certificate = models.FileField(upload_to='applications/certs/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    government_id = models.FileField(upload_to='applications/ids/', blank=True, null=True)
    blood_type = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return f"{self.donor.username} — {self.status}"


class DonationLog(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donation_logs')
    donated_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    proof_document = models.FileField(
        upload_to='donations/proofs/',
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.donor.username} donated on {self.donated_at.date()}"


class Notification(models.Model):
    NOTIF_TYPES = [
        ('approved', 'Application Approved'),
        ('rejected', 'Application Rejected'),
        ('request', 'Donation Request'),
        ('accepted', 'Request Accepted'),
        ('log_verified', 'Donation Log Verified'),
        ('log_rejected', 'Donation Log Rejected'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notif_type = models.CharField(max_length=25, choices=NOTIF_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.notif_type}"