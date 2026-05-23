#Day 2
from django.urls import path
from .views import apply_donor

urlpatterns = [
    path('apply/', apply_donor, name='apply-donor'),
]