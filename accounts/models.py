from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('recipient', 'Recipient'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='recipient')
    active_role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='recipient')
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def is_donor(self):
        return self.role == 'donor' and self.active_role == 'donor'

    def is_recipient(self):
        return self.active_role == 'recipient'

    def __str__(self):
        return f"{self.username} ({self.role})"