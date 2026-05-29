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

@login_required
def apply_donor(request):

    existing = DonorApplication.objects.filter(
        donor=request.user
    ).order_by('-submitted_at').first()

    reapply = request.GET.get("reapply")

    # APPROVED
    if existing and existing.status == DonorApplication.STATUS_APPROVED:
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
    ).select_related('donor').order_by('submitted_at')

    return render(request, 'admin/application_queue.html', {
        'applications': applications,
        'count': applications.count(),
    })

@login_required
@admin_required
def admin_review_application(request, pk):
    application = get_object_or_404(DonorApplication, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        note = request.POST.get('admin_note', '').strip()

        if action == 'approve':
            application.status = DonorApplication.STATUS_APPROVED
            application.admin_notes = note
            application.save()
            # Mark donor profile as verified
            profile = application.donor.donor_profile
            profile.is_verified = True
            profile.save()

            send_notification(
                user=application.donor,
                notif_type='approved',
                message='Your donor application has been approved! '
                        'You are now a verified donor.')

            messages.success(request, f"{application.donor.username} has been approved.")

        elif action == 'reject':
            if not note:
                messages.error(request, "Please provide a rejection reason.")
                return redirect('review_application', pk=pk)
            application.status = DonorApplication.STATUS_REJECTED
            application.admin_notes = note
            application.save()

            send_notification(
                user=application.donor,
                notif_type='rejected',
                message=f'Your donor application was not approved. '
                        f'Reason: {note}'
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
        "pending_count": DonorApplication.objects.filter(status=DonorApplication.STATUS_PENDING).count(),
        "approved_count": DonorApplication.objects.filter(status=DonorApplication.STATUS_APPROVED).count(),
        "rejected_count": DonorApplication.objects.filter(status = DonorApplication.STATUS_REJECTED).count(),
        "total_users": User.objects.count(),
        "recent_pending": recent_pending,
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
    # Only verified donors can log a donation
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

    # Check if already on cooldown
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

    # Auto-lift cooldown if it has expired
    if profile.cooldown_until and timezone.now() >= profile.cooldown_until:
        profile.is_available = True
        profile.cooldown_until = None
        profile.save()
        messages.info(request, 'Your cooldown has ended! You are now available again.')

    # Calculate days remaining
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