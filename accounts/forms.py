import json
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from django.conf import settings


def get_city_choices():
    try:
        cities_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'ph_cities.json')
        with open(cities_path, 'r') as f:
            data = json.load(f)
        cities = data.get('cities', [])
        choices = [('', '-- Select your city --')]
        choices += [(city, city) for city in cities]
        return choices
    except Exception:
        return [('', '-- Select your city --')]
    
class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('donor', 'I want to be a Donor'),
        ('recipient', 'I need blood (Recipient)'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    phone_number = forms.CharField(max_length=20, required=False)
    profile_picture = forms.ImageField(required=False)  # required=False so Django doesn't render a duplicate field; validation handled in clean_profile_picture

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2']

    def clean_profile_picture(self):
        pic = self.cleaned_data.get('profile_picture')

        if not pic:
            raise forms.ValidationError('Profile picture is required.')

        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        max_size = 5 * 1024 * 1024  # 5MB

        if pic.content_type not in allowed_types:
            raise forms.ValidationError('Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.')

        if pic.size > max_size:
            raise forms.ValidationError('File is too large. Maximum size is 5MB.')

        return pic


class ProfileSetupForm(forms.ModelForm):
    location = forms.ChoiceField(
        choices=get_city_choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-city',
            'data-placeholder': 'Search your city...',
        })
    )

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