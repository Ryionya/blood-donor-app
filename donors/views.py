#Day 2
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DonorApplicationForm
from .models import DonorApplication

@login_required
def apply_donor(request):
    # Check if user already has a pending application
    existing = DonorApplication.objects.filter(
        donor=request.user, status='pending'
    ).first()
    if existing:
        return redirect('application_submitted')

    if request.method == 'POST':
        form = DonorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.donor = request.user
            application.status = 'pending'
            application.save()
            return redirect('application_submitted')
    else:
        initial = {}
        try:
            initial['blood_type'] = request.user.donor_profile.blood_type
        except:
            pass
        form = DonorApplicationForm(initial=initial)

    return render(request, 'donors/apply.html', {'form': form})

@login_required
def application_submitted(request):
    return render(request, 'donors/application_submitted.html')
