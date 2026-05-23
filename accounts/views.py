from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileSetupForm, DonorProfileForm
from donors.models import DonorProfile


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
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_setup_view(request):
    user = request.user
    donor_profile = getattr(user, 'donor_profile', None)

    if request.method == 'POST':
        profile_form = ProfileSetupForm(request.POST, instance=user)
        donor_form = DonorProfileForm(request.POST, instance=donor_profile) if donor_profile else None

        if profile_form.is_valid():
            profile_form.save()
            if donor_form and donor_form.is_valid():
                donor_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('home')
    else:
        profile_form = ProfileSetupForm(instance=user)
        donor_form = DonorProfileForm(instance=donor_profile) if donor_profile else None

    return render(request, 'accounts/profile_setup.html', {
        'profile_form': profile_form,
        'donor_form': donor_form,
    })

@login_required
def switch_role_view(request):
    user = request.user

    # Only donors can switch
    if user.role != 'donor':
        messages.error(request, 'Only donors can switch roles.')
        return redirect('home')

    if user.active_role == 'donor':
        user.active_role = 'recipient'
        messages.info(request, 'You are now browsing as a Recipient.')
    else:
        user.active_role = 'donor'
        messages.info(request, 'You are now back in Donor mode.')

    user.save()
    return redirect('home')

def home_view(request):
    return render(request, 'home.html')