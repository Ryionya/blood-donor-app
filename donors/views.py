#Day 2
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .decorators import admin_required
from .forms import DonorApplicationForm
from .models import DonorApplication 
from django.contrib.auth import get_user_model
User = get_user_model()

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
            messages.success(request, f"{application.donor.username} has been approved.")

        elif action == 'reject':
            if not note:
                messages.error(request, "Please provide a rejection reason.")
                return redirect('review_application', pk=pk)
            application.status = DonorApplication.STATUS_REJECTED
            application.admin_notes = note
            application.save()
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