from django.urls import path
from . import views

urlpatterns = [
    path('donor/', views.donor_dashboard, name='donor_dashboard'),
    path('donor/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('donor/request/<int:request_id>/<str:action>/', views.respond_to_request, name='respond_to_request'),
]