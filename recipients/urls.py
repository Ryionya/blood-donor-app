from django.urls import path
from . import views

urlpatterns = [
    path('browse/', views.browse_donors_view, name='browse_donors'),
    path('request/<int:donor_id>/', views.send_blood_request_view, name='send_blood_request'),
    path('my-requests/', views.my_requests_view, name='my_requests'),
    path('request/manage/<int:request_id>/', views.manage_request_view, name='manage_request'),
    path('incoming-requests/', views.incoming_requests_view, name='incoming_requests'),
]