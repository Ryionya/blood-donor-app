from django import forms
from .models import DonorApplication
import os

def validate_file(file):
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    
    ext = os.path.splitext(file.name)[1].lower()
    
    if file.content_type not in allowed_types or ext not in allowed_extensions:
        raise forms.ValidationError('Only JPG, PNG, or PDF files are allowed.')
    
    if file.size > 5 * 1024 * 1024:
        raise forms.ValidationError('File size must not exceed 5MB.')

class DonorApplicationForm(forms.ModelForm):
    class Meta:
        model = DonorApplication
        fields = ['medical_certificate']
        widgets = {
            'medical_certificate': forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.pdf'}),
        }


    def clean_medical_certificate(self):
        file = self.cleaned_data.get('medical_certificate')
        if file:
            validate_file(file)
        return file