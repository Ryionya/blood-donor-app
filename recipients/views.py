from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from accounts.models import User
from donors.models import DonorProfile, Notification
from recipients.models import BloodRequest
from webpush import send_user_notification


# ─────────────────────────────────────────────
#  BROWSE / SEARCH PAGE
# ─────────────────────────────────────────────

@login_required
def browse_donors_view(request):
    donors = DonorProfile.objects.filter(
        is_verified=True,
        is_available=True,
    ).select_related('user')

    blood_type = request.GET.get('blood_type', '').strip()
    location   = request.GET.get('location',   '').strip()

    if blood_type:
        donors = donors.filter(blood_type=blood_type)
    if location:
        donors = donors.filter(location__icontains=location)

    blood_type_choices = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    return render(request, 'recipients/browse.html', {
        'donors':              donors,
        'blood_type_choices':  blood_type_choices,
        'selected_blood_type': blood_type,
        'selected_location':   location,
        'result_count':        donors.count(),
    })


# ─────────────────────────────────────────────
#  LOCATION LIST — JSON endpoint for voice parser
# ─────────────────────────────────────────────

@login_required
def location_list_view(request):
    """
    Returns all distinct non-empty locations stored in DonorProfile as JSON.
    The voice parser fetches this on page load so it can fuzzy-match
    spoken city names against real data instead of guessing free text.

    Response: { "locations": ["Calamba", "Santa Rosa", "Biñan", ...] }
    """
    locations = (
        DonorProfile.objects
        .exclude(location__isnull=True)
        .exclude(location__exact='')
        .values_list('location', flat=True)
        .distinct()
        .order_by('location')
    )
    return JsonResponse({'locations': list(locations)})


# ─────────────────────────────────────────────
#  DONOR PROFILE DETAIL
# ─────────────────────────────────────────────

@login_required
def donor_profile_view(request, donor_id):
    donor = get_object_or_404(DonorProfile, pk=donor_id, is_verified=True)

    existing_request = BloodRequest.objects.filter(
        recipient=request.user,
        donor=donor.user,
        status='pending',
    ).first()

    return render(request, 'recipients/donor_profile.html', {
        'donor':            donor,
        'existing_request': existing_request,
    })


# ─────────────────────────────────────────────
#  SEND BLOOD REQUEST
# ─────────────────────────────────────────────

@login_required
def send_request_view(request, donor_id):
    donor = get_object_or_404(
        DonorProfile, pk=donor_id, is_verified=True, is_available=True,
    )

    # Prevent donors from requesting themselves
    if request.user == donor.user:
        messages.error(request, 'You cannot send a request to yourself.')
        return redirect('browse_donors')

    existing = BloodRequest.objects.filter(
        recipient=request.user,
        donor=donor.user,
        status='pending',
    ).exists()

    if existing:
        messages.warning(request, 'You already have a pending request to this donor.')
        return redirect('donor_profile', donor_id=donor_id)

    if request.method == 'POST':
        hospital_name = request.POST.get('hospital_name', '').strip()
        urgency       = request.POST.get('urgency', 'medium')
        message       = request.POST.get('message', '').strip()

        if not hospital_name or not message:
            messages.error(request, 'Please fill in all fields.')
        else:
            BloodRequest.objects.create(
                recipient=request.user,
                donor=donor.user,
                hospital_name=hospital_name,
                urgency=urgency,
                message=message,
                status='pending',
            )

            # Push notification to donor
            try:
                payload = {
                    'head': '🩸 New Blood Request',
                    'body': f'{request.user.get_full_name() or request.user.username} needs your help at {hospital_name}.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/incoming-requests/',
                }
                send_user_notification(user=donor.user, payload=payload, ttl=1000)
            except Exception:
                pass

            # In-app notification for donor
            Notification.objects.create(
                user=donor.user,
                notif_type='request',
                message=f'{request.user.get_full_name() or request.user.username} sent you a blood donation request for {hospital_name}.',
            )

            messages.success(request, f'Request sent to {donor.user.get_full_name() or donor.user.username} successfully!')
            return redirect('my_requests')

    urgency_choices = [
        ('low',      'Low — Scheduled donation'),
        ('medium',   'Medium — Needed soon'),
        ('high',     'High — Urgent'),
        ('critical', 'Critical — Emergency'),
    ]

    return render(request, 'recipients/send_request.html', {
        'donor':           donor,
        'urgency_choices': urgency_choices,
    })


# ─────────────────────────────────────────────
#  MY REQUESTS (recipient outbox)
# ─────────────────────────────────────────────

@login_required
def my_requests_view(request):
    requests_qs = BloodRequest.objects.filter(
        recipient=request.user,
    ).select_related('donor', 'donor__donor_profile').order_by('-created_at')

    return render(request, 'recipients/my_requests.html', {
        'blood_requests': requests_qs,
    })


# ─────────────────────────────────────────────
#  INCOMING REQUESTS (donor inbox)
# ─────────────────────────────────────────────

@login_required
def incoming_requests_view(request):
    blood_requests = BloodRequest.objects.filter(
        donor=request.user,
    ).select_related('recipient').order_by('-created_at')

    return render(request, 'recipients/incoming_requests.html', {
        'blood_requests': blood_requests,
    })


# ─────────────────────────────────────────────
#  RESPOND TO REQUEST (accept / decline)
# ─────────────────────────────────────────────

@login_required
def respond_request_view(request, request_id):
    blood_request = get_object_or_404(BloodRequest, pk=request_id, donor=request.user)

    if request.method == 'POST' and blood_request.status == 'pending':
        action = request.POST.get('action')

        if action == 'accept':
            blood_request.status = 'accepted'
            blood_request.responded_at = timezone.now()
            blood_request.save()
            messages.success(request, 'You accepted the donation request.')

            # Push notification to recipient
            try:
                payload = {
                    'head': '✅ Donation Request Accepted!',
                    'body': f'{request.user.get_full_name() or request.user.username} accepted your blood request. Check their contact info now.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/my-requests/',
                }
                send_user_notification(user=blood_request.recipient, payload=payload, ttl=1000)
            except Exception:
                pass

            # In-app notification for recipient
            Notification.objects.create(
                user=blood_request.recipient,
                notif_type='accepted',
                message=f'{request.user.get_full_name() or request.user.username} accepted your blood request. Contact info is now available.',
            )

        elif action == 'decline':
            blood_request.status = 'declined'
            blood_request.responded_at = timezone.now()
            blood_request.save()
            messages.info(request, 'You declined the donation request.')

            # Push notification to recipient
            try:
                payload = {
                    'head': '❌ Donation Request Declined',
                    'body': 'Your blood request was declined. Try finding another donor.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/browse/',
                }
                send_user_notification(user=blood_request.recipient, payload=payload, ttl=1000)
            except Exception:
                pass

            # In-app notification for recipient
            Notification.objects.create(
                user=blood_request.recipient,
                notif_type='rejected',
                message=f'{request.user.get_full_name() or request.user.username} declined your blood request.',
            )

    return redirect('incoming_requests')