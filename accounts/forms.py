from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile

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
        fields = ['first_name', 'last_name', 'phone_number', 'location', 'profile_picture']


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['blood_type', 'bio']


class RecipientProfileForm(forms.ModelForm):
    class Meta:
        model = RecipientProfile
        fields = ['government_id', 'blood_type']
        widgets = {
            'government_id': forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.pdf'}),
        }