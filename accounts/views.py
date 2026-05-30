from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileSetupForm, DonorProfileForm, RecipientProfileForm
from donors.models import DonorProfile
from recipients.models import RecipientProfile


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
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
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-create DonorProfile if registering as donor
            if user.role == 'donor':
                DonorProfile.objects.create(user=user)
            elif user.role == 'recipient':
                RecipientProfile.objects.create(user=user)
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

              # Remember Me — 30 days
            if request.POST.get('remember_me'):
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days in seconds
            else:
                request.session.set_expiry(0)  # expires when browser closes
                
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
    recipient_profile = getattr(user, 'recipient_profile', None)

    if request.method == 'POST':
        profile_form = ProfileSetupForm(
            request.POST,
            request.FILES,
            instance=user
        )

        donor_form = DonorProfileForm(
            request.POST,
            instance=donor_profile
        ) if donor_profile else None

        recipient_form = RecipientProfileForm(
            request.POST,
            request.FILES,
            instance=recipient_profile
        ) if recipient_profile else None

        if profile_form.is_valid():
            profile_form.save()

            if donor_form and donor_form.is_valid():
                donor_form.save()

            if recipient_form and recipient_form.is_valid():
                recipient_form.save()

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
    })


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