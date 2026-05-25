from django.urls import path
from . import views

urlpatterns = [
    path('browse/', views.browse_donors_view, name='browse_donors'),
]