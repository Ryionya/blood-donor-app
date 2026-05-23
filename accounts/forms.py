from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from donors.models import DonorProfile

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('donor', 'I want to be a Donor'),
        ('recipient', 'I need blood (Recipient)'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2']


class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'location']


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['blood_type', 'bio']