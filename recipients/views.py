from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import BloodRequest
from accounts.models import User
from webpush import send_user_notification
from donors.models import Notification


def browse_donors_view(request):
    # Placeholder donor data for now
    # M3 Day 3 will replace this with real database queries
    placeholder_donors = [
        {
            'name': 'Juan dela Cruz',
            'blood_type': 'A+',
            'location': 'Santa Rosa, Laguna',
            'is_available': True,
            'bio': 'Happy to help anyone in need.',
        },
        {
            'name': 'Maria Santos',
            'blood_type': 'O-',
            'location': 'Calamba, Laguna',
            'is_available': True,
            'bio': 'Regular donor since 2020.',
        },
        {
            'name': 'Carlo Reyes',
            'blood_type': 'B+',
            'location': 'Biñan, Laguna',
            'is_available': False,
            'bio': 'Currently on cooldown period.',
        },
        {
            'name': 'Ana Lim',
            'blood_type': 'AB+',
            'location': 'San Pedro, Laguna',
            'is_available': True,
            'bio': 'Type AB+ universal plasma donor.',
        },
        {
            'name': 'Ramon Garcia',
            'blood_type': 'O+',
            'location': 'Santa Rosa, Laguna',
            'is_available': True,
            'bio': 'Available on weekends.',
        },
        {
            'name': 'Sofia Torres',
            'blood_type': 'A-',
            'location': 'Cabuyao, Laguna',
            'is_available': False,
            'bio': 'Currently unavailable.',
        },
    ]

    # Basic filtering from GET params (placeholder logic)
    blood_type = request.GET.get('blood_type', '')
    location = request.GET.get('location', '')

    if blood_type:
        placeholder_donors = [d for d in placeholder_donors if d['blood_type'] == blood_type]
    if location:
        placeholder_donors = [d for d in placeholder_donors if location.lower() in d['location'].lower()]

    blood_type_choices = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    return render(request, 'recipients/browse.html', {
        'donors': placeholder_donors,
        'blood_type_choices': blood_type_choices,
        'selected_blood_type': blood_type,
        'selected_location': location,
    })
    
@login_required
def send_blood_request_view(request, donor_id):
    donor = get_object_or_404(User, id=donor_id, role='donor')

    # Prevent donors from requesting themselves
    if request.user == donor:
        messages.error(request, 'You cannot send a request to yourself.')
        return redirect('browse_donors')

    # Check if there is already a pending request to this donor
    existing_request = BloodRequest.objects.filter(
        recipient=request.user,
        donor=donor,
        status='pending'
    ).first()

    if existing_request:
        messages.warning(request, 'You already have a pending request to this donor.')
        return redirect('browse_donors')

    if request.method == 'POST':
        hospital_name = request.POST.get('hospital_name')
        urgency = request.POST.get('urgency')
        message = request.POST.get('message')

        if not hospital_name or not urgency or not message:
            messages.error(request, 'Please fill in all fields.')
        else:
            BloodRequest.objects.create(
                recipient=request.user,
                donor=donor,
                hospital_name=hospital_name,
                urgency=urgency,
                message=message,
                status='pending'
            )
            
            # Notify the donor
            try:
                payload = {
                    'head': '🩸 New Blood Request',
                    'body': f'{request.user.get_full_name() or request.user.username} needs your help at {hospital_name}.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/incoming-requests/',
                }
                send_user_notification(user=donor, payload=payload, ttl=1000)
            except Exception:
                pass
            
            # Create in-app notification for donor
            Notification.objects.create(
                user=donor,
                notif_type='request',
                message=f'{request.user.get_full_name() or request.user.username} sent you a blood donation request for {hospital_name}.',
            )
            
            messages.success(request, f'Request sent to {donor.get_full_name() or donor.username} successfully!')
            return redirect('my_requests')

    return render(request, 'recipients/send_request.html', {
        'donor': donor,
        'urgency_choices': BloodRequest._meta.get_field('urgency').choices,
    })
    
@login_required
def my_requests_view(request):
    # For recipients — requests they sent
    sent_requests = BloodRequest.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    return render(request, 'recipients/my_requests.html', {
        'sent_requests': sent_requests,
    })
    
@login_required
def manage_request_view(request, request_id):
    # For donors — accept or decline incoming requests
    blood_request = get_object_or_404(BloodRequest, id=request_id, donor=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            blood_request.status = 'accepted'
            blood_request.responded_at = timezone.now()
            blood_request.save()
            messages.success(request, 'You accepted the donation request.')
            
            # Notify the recipient
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
            
            # Create in-app notification for recipient
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
            
            # Notify the recipient
            try:
                payload = {
                    'head': '❌ Donation Request Declined',
                    'body': f'Your blood request was declined. Try finding another donor.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/browse/',
                }
                send_user_notification(user=blood_request.recipient, payload=payload, ttl=1000)
            except Exception:
                pass
            
            # Create in-app notification for recipient
            Notification.objects.create(
                user=blood_request.recipient,
                notif_type='rejected',
                message=f'{request.user.get_full_name() or request.user.username} declined your blood request.',
            )

    return redirect('incoming_requests')

@login_required
def incoming_requests_view(request):
    # For donors — requests they received
    incoming = BloodRequest.objects.filter(
        donor=request.user
    ).order_by('-created_at')

    return render(request, 'recipients/incoming_requests.html', {
        'incoming_requests': incoming,
    })