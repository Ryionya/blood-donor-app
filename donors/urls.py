#Day 2
from django.urls import path
from .views import apply_donor
from . import views

urlpatterns = [
    path('apply/', views.apply_donor, name='apply_donor'),
    path('apply/submitted/', views.application_submitted, name='application_submitted'),
]