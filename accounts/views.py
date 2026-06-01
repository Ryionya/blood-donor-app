from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileSetupForm, DonorProfileForm, RecipientProfileForm
from donors.models import DonorProfile, DonorApplication
from recipients.models import RecipientProfile
from donors.utils import send_notification
from django.utils import timezone

def check_verification_expiry(user):
    try:
        profile = user.donor_profile
        if profile.is_verified and profile.verification_expires_at:
            if timezone.now() >= profile.verification_expires_at:
                profile.is_verified = False
                profile.verified_at = None
                profile.verification_expires_at = None
                profile.save()
                send_notification(
                    user=user,
                    notif_type='rejected',
                    message='Your donor verification has expired (3 months). '
                            'Please reapply to become a verified donor again.',
                )
    except:
        pass


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role == 'donor':
        check_verification_expiry(request.user)  # safe — user is authenticated here

    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'donor':
        return redirect('cooldown_status')
    elif request.user.role == 'recipient':
        return redirect('browse_donors')

    return render(request, 'home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            if user.role == 'donor':
                DonorProfile.objects.create(user=user)
            elif user.role == 'recipient':
                RecipientProfile.objects.create(user=user)
            user.profile_picture = form.cleaned_data['profile_picture']
            user.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Please complete your profile.')
            return redirect('profile_setup')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if request.POST.get('remember_me'):
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                request.session.set_expiry(0)
                
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile_setup_view(request):
    user = request.user

    donor_profile = getattr(user, 'donor_profile', None)
    recipient_profile = getattr(user, 'recipient_profile', None) if user.role == 'recipient' else None

    if request.method == 'POST':
        profile_form = ProfileSetupForm(
            request.POST,
            request.FILES,
            instance=user
        )

        donor_form = DonorProfileForm(
            request.POST,
            request.FILES,
            instance=donor_profile
        ) if donor_profile else None

        recipient_form = RecipientProfileForm(
            request.POST,
            request.FILES,
            instance=recipient_profile
        ) if recipient_profile else None

        # Handle profile picture removal
        if request.POST.get('remove_profile_picture') == '1':
            if user.profile_picture:
                user.profile_picture.delete(save=False)
                user.profile_picture = None
                user.save()
            messages.success(request, 'Profile picture removed.')
            return redirect('profile_setup')

        # Validate profile picture upload
        if 'profile_picture' in request.FILES:
            pic = request.FILES['profile_picture']
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            max_size = 5 * 1024 * 1024  # 5MB
            if pic.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.')
                return redirect('profile_setup')
            if pic.size > max_size:
                messages.error(request, 'File is too large. Maximum size is 5MB.')
                return redirect('profile_setup')

        profile_form = ProfileSetupForm(request.POST, request.FILES, instance=user)
        if profile_form.is_valid():
            profile_form.save()

        if donor_form and donor_form.is_valid():
            donor_instance = donor_form.save(commit=False)


            if donor_profile and donor_profile.is_verified:
                donor_instance.blood_type = donor_profile.blood_type
            
            # Handle government ID upload
            if 'donor_government_id' in request.FILES:
                donor_instance.government_id = request.FILES['donor_government_id']

            donor_instance.save()

        if recipient_form and recipient_form.is_valid():
            recipient_instance = recipient_form.save(commit=False)
            if 'government_id' in request.FILES:
                recipient_instance.government_id = request.FILES['government_id']
            else:
                recipient_instance.government_id = recipient_profile.government_id
            recipient_instance.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('home')

    else:
        profile_form = ProfileSetupForm(instance=user)

        donor_form = DonorProfileForm(
            instance=donor_profile
        ) if donor_profile else None

        recipient_form = RecipientProfileForm(
            instance=recipient_profile
        ) if recipient_profile else None

    return render(request, 'accounts/profile_setup.html', {
        'profile_form': profile_form,
        'donor_form': donor_form,
        'recipient_form': recipient_form,
        'donor_profile': donor_profile,
    })

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password was updated successfully!')
            return redirect('profile_setup')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
 
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def switch_role_view(request):
    user = request.user
    if user.role != 'donor':
        messages.error(request, 'Only donors can switch roles.')
        return redirect('home')
    if user.active_role == 'donor':
        user.active_role = 'recipient'
        user.save()
        messages.info(request, 'You are now browsing as a Recipient.')
        return redirect('browse_donors')
    else:
        user.active_role = 'donor'
        user.save()
        messages.info(request, 'You are now back in Donor mode.')
        return redirect('cooldown_status')

@login_required
def faq_view(request):
    return render(request, 'faq.html')