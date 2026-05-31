from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from accounts.models import User
from donors.models import DonorProfile, Notification
from recipients.models import BloodRequest, RecipientProfile
from webpush import send_user_notification

import json
from core.groq_service import parse_voice_intent, get_donor_recommendation
from django.urls import reverse

import json as json_module
from django.conf import settings
import os



# ─────────────────────────────────────────────
#  COMPATIBILITY MATRIX
# ─────────────────────────────────────────────

COMPATIBLE_DONORS = {
    'A+':  ['A+', 'A-', 'O+', 'O-'],
    'A-':  ['A-', 'O-'],
    'B+':  ['B+', 'B-', 'O+', 'O-'],
    'B-':  ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'AB-': ['A-', 'B-', 'AB-', 'O-'],
    'O+':  ['O+', 'O-'],
    'O-':  ['O-'],
}

# ─────────────────────────────────────────────
#  BROWSE / SEARCH PAGE
# ─────────────────────────────────────────────

@login_required
def browse_donors_view(request):
    blood_type = request.GET.get('blood_type', '')
    location   = request.GET.get('location', '')

    # ── Auto-detect the logged-in user's blood type ───────────────────
    # Works for both donors and recipients since either can need blood.
    # We check DonorProfile first, then RecipientProfile as fallback.
    user_blood_type = ''
    try:
        user_blood_type = request.user.donor_profile.blood_type or ''
    except Exception:
        pass

    if not user_blood_type:
        try:
            user_blood_type = request.user.recipient_profile.blood_type or ''
        except Exception:
            pass

    # ── Base queryset ─────────────────────────────────────────────────
    donors = DonorProfile.objects.filter(
        is_verified=True,
        is_available=True,
    ).exclude(user=request.user).select_related('user')

    # ── Blood type compatibility filter ───────────────────────────────
    # 'search_blood_type' ang gagamitin sa filter query at AI recommendation.
    # Kapag walang pinili sa filter UI, gagamitin ang user_blood_type para tugma pa rin ang listahan at AI.
    search_blood_type = blood_type or user_blood_type

    if search_blood_type:
        compatible_types = COMPATIBLE_DONORS.get(search_blood_type, [search_blood_type])
        donors = donors.filter(blood_type__in=compatible_types)

    # ── Location filter ───────────────────────────────────────────────
    if location:
        donors = donors.filter(location__icontains=location)

    # ── AI Recommendation ─────────────────────────────────────────────
    ai_recommendation = None
    if donors.exists() and (search_blood_type or location):
        try:
            ai_recommendation = get_donor_recommendation(
                donors=list(donors),
                blood_type_needed=search_blood_type,
                location=location
            )
        except Exception:
            pass

    # ── Philippine cities for dropdown ────────────────────────────────
    try:
        cities_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'ph_cities.json')
        with open(cities_path, 'r') as f:
            ph_cities = json_module.load(f).get('cities', [])
    except Exception:
        ph_cities = []

    blood_type_choices = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    return render(request, 'recipients/browse.html', {
        'donors':              donors,
        'blood_type_choices':  blood_type_choices,
        'selected_blood_type': blood_type,         # Blanko ('') para "All Blood Types" ang dropdown selection sa screen
        'display_blood_type':  search_blood_type,  # Ipapadala ito para sa red banner/badge na nagpapakita ng hinahanap na blood type
        'selected_location':   location,
        'ph_cities':           ph_cities,
        'ai_recommendation':   ai_recommendation,
        'result_count':        donors.count(),
        'user_blood_type':     user_blood_type,
    })


# ─────────────────────────────────────────────
#  LOCATION LIST — JSON endpoint for voice parser
# ─────────────────────────────────────────────

@login_required
def location_list_view(request):
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
        status__in=['pending_admin', 'pending'],
    ).first()

    accepted_request = BloodRequest.objects.filter(
        recipient=request.user,
        donor=donor.user,
        status='accepted',
    ).exists()

    return render(request, 'recipients/donor_profile.html', {
        'donor':            donor,
        'existing_request': existing_request,
        'accepted_request': accepted_request,
    })


# ─────────────────────────────────────────────
#  SEND BLOOD REQUEST
# ─────────────────────────────────────────────

@login_required
def send_request_view(request, donor_id):
    donor = get_object_or_404(
        DonorProfile, pk=donor_id, is_verified=True, is_available=True,
    )

    if request.user == donor.user:
        messages.error(request, 'You cannot send a request to yourself.')
        return redirect('browse_donors')

    # Check government ID
    recipient_profile, created = RecipientProfile.objects.get_or_create(user=request.user)
    if request.user.role == 'donor':
        has_gov_id = bool(request.user.donor_profile.government_id)
    else:
        has_gov_id = bool(recipient_profile.government_id)

    if not has_gov_id:
        messages.error(request, 'You must upload a Government ID in your profile before sending a blood request.')
        return redirect('profile_setup')

    existing = BloodRequest.objects.filter(
        recipient=request.user,
        donor=donor.user,
        status__in=['pending_admin', 'pending'],
    ).exists()

    if existing:
        messages.warning(request, 'You already have a pending request to this donor.')
        return redirect('donor_profile', donor_id=donor_id)

    if request.method == 'POST':
        hospital_name  = request.POST.get('hospital_name', '').strip()
        needed_by_date = request.POST.get('needed_by_date', '').strip()
        blood_bags     = request.POST.get('blood_bags', '1').strip()
        message        = request.POST.get('message', '').strip()
        medical_cert   = request.FILES.get('medical_certificate')

        # Validate
        if not hospital_name or not message or not needed_by_date:
            messages.error(request, 'Please fill in all required fields.')
        elif not medical_cert:
            messages.error(request, 'Please attach a medical certificate.')
        else:
            from datetime import date as date_type
            try:
                needed_by = date_type.fromisoformat(needed_by_date)
                if needed_by < date_type.today():
                    messages.error(request, 'Needed-by date cannot be in the past.')
                    return render(request, 'recipients/send_request.html', {'donor': donor})
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return render(request, 'recipients/send_request.html', {'donor': donor})

            try:
                bags = int(blood_bags)
                if bags < 1:
                    raise ValueError
            except ValueError:
                bags = 1

            blood_request = BloodRequest.objects.create(
                recipient=request.user,
                donor=donor.user,
                hospital_name=hospital_name,
                needed_by_date=needed_by,
                blood_bags=bags,
                message=message,
                medical_certificate=medical_cert,
                status='pending_admin',
            )

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

            Notification.objects.create(
                user=donor.user,
                notif_type='request',
                message=f'{request.user.get_full_name() or request.user.username} sent you a blood donation request for {hospital_name}.',
            )

            messages.success(request, 'Request sent successfully!')
            return redirect('my_requests')

    return render(request, 'recipients/send_request.html', {
        'donor': donor,
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

            Notification.objects.create(
                user=blood_request.recipient,
                notif_type='rejected',
                message=f'{request.user.get_full_name() or request.user.username} declined your blood request.',
            )

    return redirect('incoming_requests')


# ─────────────────────────────────────────────
#  VOICE INTENT API VIEW
# ─────────────────────────────────────────────

@login_required
def voice_intent_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        transcript = data.get('transcript', '')
        if not transcript:
            return JsonResponse({'type': 'unknown'})

        intent = parse_voice_intent(
            transcript=transcript,
            user_role=request.user.role,
            active_role=request.user.active_role
        )

        if intent.get('type') == 'navigate':
            page = intent.get('page')
            try:
                url = reverse(page)
                intent['url'] = url
            except Exception:
                intent['type'] = 'unknown'

        if intent.get('type') == 'logout':
            intent['url'] = reverse('logout')

        return JsonResponse(intent)

    except Exception as e:
        return JsonResponse({'type': 'unknown'})


def ph_cities_view(request):
    try:
        cities_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'ph_cities.json')
        with open(cities_path, 'r') as f:
            data = json_module.load(f)
        return JsonResponse(data)
    except Exception:
        return JsonResponse({'cities': []})