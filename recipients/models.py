from django.db import models
from django.conf import settings
from datetime import date


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

    recipient           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    donor               = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    hospital_name       = models.CharField(max_length=200)
    needed_by_date      = models.DateField(null=True, blank=True)       # replaces urgency
    blood_bags          = models.PositiveIntegerField(default=1)         # new field
    message             = models.TextField()
    medical_certificate = models.FileField(upload_to='requests/certs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_admin')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    recipient_government_id = models.FileField(upload_to='requests/recipient_ids/', blank=True, null=True)
    donor_government_id = models.FileField(upload_to='requests/donor_ids/', blank=True, null=True)


    @property
    def urgency(self):
        """Auto-determine urgency from needed_by_date."""
        if not self.needed_by_date:
            return 'medium'
        days_left = (self.needed_by_date - date.today()).days
        if days_left <= 1:
            return 'critical'
        elif days_left <= 3:
            return 'high'
        elif days_left <= 7:
            return 'medium'
        else:
            return 'low'

    @property
    def urgency_display(self):
        labels = {
            'critical': '🔴 Critical — Emergency',
            'high':     '🟠 High — Urgent',
            'medium':   '🟡 Medium — Needed soon',
            'low':      '🟢 Low — Scheduled donation',
        }
        return labels.get(self.urgency, 'Unknown')

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
    blood_type_locked = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.user.username} — Recipient Profile"
    
class ChatMessage(models.Model):
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"