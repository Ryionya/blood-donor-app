from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
        
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
             raise ValueError("Username is required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("active_role", "admin")

        return self.create_user(username, email, password, **extra_fields)
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
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    objects = CustomUserManager()
    def is_donor(self):
        return self.role == 'donor' and self.active_role == 'donor'

    def is_recipient(self):
        return self.active_role == 'recipient'

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    