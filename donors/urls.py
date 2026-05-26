#Day 2
from django.urls import path
from .views import apply_donor
from . import views

urlpatterns = [
    path('apply/', views.apply_donor, name='apply_donor'),
    path('apply/submitted/', views.application_submitted, name='application_submitted'),
    path('admin-panel/queue/', views.admin_application_queue, name='admin_application_queue'),
    path('admin-panel/review/<int:pk>/', views.admin_review_application, name='review_application'),
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('my-application/', views.my_application, name='my_application'),
    path('log-donation/', views.log_donation_view, name='log_donation'),
    path('cooldown-status/', views.cooldown_status_view, name='cooldown_status'),
]