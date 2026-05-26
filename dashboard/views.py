from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from recipients.models import BloodRequest

@login_required
def donor_dashboard(request):
    donor_profile = request.user.donor_profile
    incoming_requests = BloodRequest.objects.filter(
        donor=request.user
    ).order_by('-created_at')

    context = {
        'donor_profile': donor_profile,
        'incoming_requests': incoming_requests,
    }
    return render(request, 'dashboard/donor_dashboard.html', context)


@login_required
def toggle_availability(request):
    if request.method == 'POST':
        profile = request.user.donor_profile
        if not profile.is_on_cooldown():
            profile.is_available = not profile.is_available
            profile.save()
    return redirect('donor_dashboard')


@login_required
def respond_to_request(request, request_id, action):
    if request.method == 'POST':
        blood_request = get_object_or_404(BloodRequest, id=request_id, donor=request.user)
        if action == 'accept':
            blood_request.status = 'accepted'
        elif action == 'decline':
            blood_request.status = 'declined'
        blood_request.responded_at = timezone.now()
        blood_request.save()
    return redirect('donor_dashboard')