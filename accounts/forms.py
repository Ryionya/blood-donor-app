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
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'location', 'profile_picture']


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['blood_type', 'bio']