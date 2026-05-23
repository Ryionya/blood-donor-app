#Day 2
from django.shortcuts import render, redirect
from .forms import DonorApplicationForm

def apply_donor(request):
    if request.method == 'POST':
        form = DonorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.status = 'pending'
            app.save()
            return redirect('application-success')
    else:
        form = DonorApplicationForm()

    return render(request, 'donors/apply.html', {'form': form})