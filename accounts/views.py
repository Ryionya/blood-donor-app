from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

def home_view(request):
    if request.user.is_authenticated:
        return redirect('browse')
    return redirect('login')

def register_view(request):
    return render(request, 'accounts/register.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def profile_setup_view(request):
    return render(request, 'accounts/profile_setup.html')