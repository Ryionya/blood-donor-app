from django.db import models
from django.conf import settings

URGENCY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

BLOOD_TYPE_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]


class BloodRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_admin', 'Pending Admin Review'),
        ('pending', 'Pending Donor Response'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('rejected_by_admin', 'Rejected by Admin'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    hospital_name = models.CharField(max_length=200)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    message = models.TextField()
    medical_certificate = models.FileField(upload_to='requests/certs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_admin')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    recipient_government_id = models.FileField(upload_to='requests/recipient_ids/', blank=True, null=True)
    donor_government_id = models.FileField(upload_to='requests/donor_ids/', blank=True, null=True)

    def __str__(self):
        return f"{self.recipient.username} → {self.donor.username} ({self.status})"
    


class RecipientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipient_profile'
    )
    government_id = models.FileField(
        upload_to='recipient/ids/',
        blank=True,
        null=True
    )
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPE_CHOICES)

    def __str__(self):
        return f"{self.user.username} — Recipient Profile"