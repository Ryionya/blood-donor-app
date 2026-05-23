#Day 2
from django import forms
from .models import DonorApplication

class DonorApplicationForm(forms.ModelForm):
    class Meta:
        model = DonorApplication
        fields = ['government_id', 'medical_certificate']