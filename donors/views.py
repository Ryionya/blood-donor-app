#Day 2
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from .decorators import admin_required
from .forms import DonorApplicationForm
from .models import DonorApplication, DonorProfile, DonationLog 
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import Notification
from .utils import send_notification
from recipients.models import BloodRequest
from accounts.models import User
from datetime import timedelta
from django.utils import timezone


@login_required
def apply_donor(request):
    # Check if profile is complete
    profile = request.user.donor_profile
    if not profile.blood_type or not profile.government_id:
        messages.error(request, 'Please complete your profile first — blood type and government ID are required before applying.')
        return redirect('profile_setup')

    existing = DonorApplication.objects.filter(
        donor=request.user
    ).order_by('-submitted_at').first()

    reapply = request.GET.get("reapply")

    # APPROVED — but only block if still verified
    if existing and existing.status == DonorApplication.STATUS_APPROVED and profile.is_verified:
        return redirect('my_application')

    # UNVERIFIED — allow reapply
    if existing and existing.status == DonorApplication.STATUS_UNVERIFIED and not reapply:
        return redirect('my_application')

    # PENDING
    if existing and existing.status == DonorApplication.STATUS_PENDING:
        return redirect('application_submitted')

    # REJECTED
    if (
        existing
        and existing.status == DonorApplication.STATUS_REJECTED
        and not reapply
    ):
        return redirect('my_application')

    if request.method == 'POST':
        form = DonorApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.donor = request.user
            application.status = DonorApplication.STATUS_PENDING
            application.government_id = request.user.donor_profile.government_id
            application.save()

            return redirect('application_submitted')

    else:
        form = DonorApplicationForm()

    return render(request, 'donors/apply.html', {'form': form})


@login_required
def application_submitted(request):
    return render(request, 'donors/application_submitted.html')


#Day 3
@login_required
@admin_required
def admin_application_queue(request):
    applications = DonorApplication.objects.filter(
        status='pending'
    ).select_related('donor').order_by('-submitted_at')

    return render(request, 'admin/application_queue.html', {
        'applications': applications,
        'count': applications.count(),
    })

@login_required
@admin_required
def admin_review_application(request, pk):
    application = get_object_or_404(DonorApplication, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('admin_note', '').strip()
        flag_user = request.POST.get('flag_user')

        if flag_user:
            application.donor.is_flagged = True
            application.donor.save()
            messages.warning(request, f"{application.donor.username} has been flagged for suspicious behavior.")

        if action == 'approve':
            application.status = DonorApplication.STATUS_APPROVED
            application.admin_notes = note
            application.reviewed_at = timezone.now()
            application.save()

            profile = application.donor.donor_profile
            profile.is_verified = True
            profile.verified_at = timezone.now()
            profile.verification_expires_at = timezone.now() + timedelta(days=90)
            profile.save()

            local_expires = timezone.localtime(profile.verification_expires_at)

            send_notification(
                user=application.donor,
                notif_type='approved',
                message=f'Your donor application has been approved! You are now a verified donor. '
                        f'Your verification is valid for 3 months until '
                        f'{local_expires.strftime("%B %d, %Y")}.'
            )
            messages.success(request, f"{application.donor.username} has been approved.")

        elif action == 'reject':
            if not note:
                messages.error(request, 'Please provide a rejection reason.')
                return redirect('review_application', pk=pk)

            application.status = DonorApplication.STATUS_REJECTED
            application.admin_notes = note
            application.reviewed_at = timezone.now()
            application.save()

            send_notification(
                user=application.donor,
                notif_type='rejected',
                message=f'Your donor application was not approved. Reason: {note}'
            )
            messages.warning(request, f"{application.donor.username} has been rejected.")

        return redirect('admin_application_queue')

    return render(request, 'admin/review_application.html', {
        'application': application
    })


@login_required
@admin_required
def admin_dashboard(request):
    recent_pending = DonorApplication.objects.filter(
        status=DonorApplication.STATUS_PENDING
    ).order_by("-submitted_at")[:3]

    context = {
        "pending_count": DonorApplication.objects.filter(
            status=DonorApplication.STATUS_PENDING
        ).count(),
        "approved_count": DonorProfile.objects.filter(is_verified=True).count(),
        "rejected_count": DonorApplication.objects.filter(status=DonorApplication.STATUS_REJECTED).count(),
        "total_users": User.objects.filter(role__in=['donor', 'recipient']).count(),
        "recent_pending": recent_pending,
        "pending_requests_count": BloodRequest.objects.filter(status='pending_admin').count(),
    }

    return render(request, "admin/dashboard.html", context)


@login_required
def my_application(request):
    app = DonorApplication.objects.filter(
        donor=request.user
    ).order_by('-submitted_at').first()

    return render(request, "donors/my_application.html", {
        "app": app
    })


@login_required
def log_donation_view(request):
    if request.user.role != 'donor':
        messages.error(request, 'Only donors can log a donation.')
        return redirect('home')

    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        messages.error(request, 'Donor profile not found.')
        return redirect('home')

    if not profile.is_verified:
        messages.error(request, 'Only verified donors can log a donation.')
        return redirect('home')

    if profile.is_on_cooldown():
        messages.warning(request, f'You are currently on cooldown until {profile.cooldown_until.strftime("%B %d, %Y")}.')
        return redirect('cooldown_status')

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        DonationLog.objects.create(
            donor=request.user,
            notes=notes
        )
        messages.success(request, 'Donation logged! You are now on a 56-day cooldown.')
        return redirect('cooldown_status')

    return render(request, 'donors/log_donation.html', {
        'profile': profile,
    })


@login_required
def cooldown_status_view(request):
    if request.user.role != 'donor':
        messages.error(request, 'Only donors can view cooldown status.')
        return redirect('home')

    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        messages.error(request, 'Donor profile not found.')
        return redirect('home')

    donation_logs = DonationLog.objects.filter(
        donor=request.user
    ).order_by('-donated_at')

    if profile.cooldown_until and timezone.now() >= profile.cooldown_until:
        profile.is_available = True
        profile.cooldown_until = None
        profile.save()
        messages.info(request, 'Your cooldown has ended! You are now available again.')

    days_remaining = None
    if profile.is_on_cooldown():
        delta = profile.cooldown_until - timezone.now()
        days_remaining = delta.days

    return render(request, 'donors/cooldown_status.html', {
        'profile': profile,
        'donation_logs': donation_logs,
        'days_remaining': days_remaining,
    })


#Day 4
@login_required
def mark_notifications_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    from django.http import JsonResponse
    return JsonResponse({'status': 'ok'})


@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'notifications/all.html', {
        'notifications': notifications,
    })


@login_required
def mark_single_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    next_url = request.GET.get('next', '/my-application/')
    return redirect(next_url)


@login_required
@admin_required
def admin_manage_users(request):
    users = User.objects.all().order_by('date_joined')
    return render(request, 'admin/manage_users.html', {'users': users})


@login_required
@admin_required
def admin_donor_list(request):
    donors = DonorProfile.objects.filter(
        is_verified=True
    ).select_related('user').order_by('user__date_joined')
    return render(request, 'admin/donor_list.html', {'donors': donors})


@login_required
@admin_required
def admin_stats(request):
    from recipients.models import BloodRequest
    from donors.models import DonationLog

    context = {
        'total_requests': BloodRequest.objects.count(),
        'pending_requests': BloodRequest.objects.filter(status='pending').count(),
        'accepted_requests': BloodRequest.objects.filter(status='accepted').count(),
        'declined_requests': BloodRequest.objects.filter(status='declined').count(),
        'total_donations': DonationLog.objects.count(),
    }
    return render(request, 'admin/stats.html', context)


@login_required
@admin_required
def admin_request_queue(request):
    requests = BloodRequest.objects.filter(
        status='pending_admin'
    ).select_related('recipient', 'donor').order_by('-created_at')

    return render(request, 'admin/request_queue.html', {
        'requests': requests,
        'count': requests.count(),
    })


@login_required
@admin_required
def admin_review_request(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('admin_note', '').strip()

        if action == 'approve':
            blood_request.status = 'pending'
            blood_request.admin_notes = note
            blood_request.save()

            send_notification(
                user=blood_request.donor,
                notif_type='request',
                message=f'{blood_request.recipient.get_full_name() or blood_request.recipient.username} sent you a blood donation request for {blood_request.hospital_name}.',
            )

            try:
                from webpush import send_user_notification
                payload = {
                    'head': '🩸 New Blood Request',
                    'body': f'{blood_request.recipient.get_full_name() or blood_request.recipient.username} needs your help at {blood_request.hospital_name}.',
                    'icon': '/static/images/icon-192.png',
                    'url': '/incoming-requests/',
                }
                send_user_notification(user=blood_request.donor, payload=payload, ttl=1000)
            except Exception:
                pass

            send_notification(
                user=blood_request.recipient,
                notif_type='request_approved',
                message=f'Your blood request to {blood_request.donor.username} has been verified and forwarded to the donor.',
            )

            messages.success(request, 'Request approved and forwarded to donor.')

        elif action == 'reject':
            if not note:
                messages.error(request, 'Please provide a rejection reason.')
                return redirect('admin_review_request', pk=pk)

            blood_request.status = 'rejected_by_admin'
            blood_request.admin_notes = note
            blood_request.save()

            send_notification(
                user=blood_request.recipient,
                notif_type='request_rejected',
                message=f'Your blood request was not approved by admin. Reason: {note}',
            )

            messages.warning(request, 'Request rejected.')

        return redirect('admin_request_queue')

    return render(request, 'admin/review_request.html', {
        'blood_request': blood_request,
    })


@login_required
@admin_required
def admin_user_list(request):
    users = User.objects.exclude(role='admin').order_by('-date_joined')
    return render(request, 'admin/user_list.html', {
        'users': users,
        'total_donors': User.objects.filter(role='donor').count(),
        'total_recipients': User.objects.filter(role='recipient').count(),
    })


@login_required
@admin_required
def admin_user_profile(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    donor_profile = getattr(profile_user, 'donor_profile', None)
    recipient_profile = getattr(profile_user, 'recipient_profile', None)
    applications = DonorApplication.objects.filter(donor=profile_user).order_by('-submitted_at')
    requests = BloodRequest.objects.filter(recipient=profile_user).order_by('-created_at')

    return render(request, 'admin/user_profile.html', {
        'profile_user': profile_user,
        'donor_profile': donor_profile,
        'recipient_profile': recipient_profile,
        'applications': applications,
        'requests': requests,
    })