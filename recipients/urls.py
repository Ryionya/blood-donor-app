from django.urls import path
from . import views

urlpatterns = [
    path('browse/',                 views.browse_donors_view,  name='browse_donors'),
    path('locations/',              views.location_list_view,  name='location_list'),
    path('donor/<int:donor_id>/',   views.donor_profile_view,  name='donor_profile'),
    path('request/<int:donor_id>/', views.send_request_view,   name='send_request'),
    path('my-requests/',            views.my_requests_view,    name='my_requests'),
    path('incoming/',               views.incoming_requests_view, name='incoming_requests'),
    path('respond/<int:request_id>/', views.respond_request_view,   name='respond_request'),
    path('voice-intent/', views.voice_intent_view, name='voice_intent'),
    path('ph-cities/', views.ph_cities_view, name='ph_cities'),
]
