from django.urls import path
from . import views

urlpatterns = [
    # Donor application
    path('apply/',                          views.apply_donor,                  name='apply_donor'),
    path('apply/submitted/',                views.application_submitted,        name='application_submitted'),
    path('my-application/',                 views.my_application,               name='my_application'),

    # Admin panel
    path('admin-panel/queue/',              views.admin_application_queue,      name='admin_application_queue'),
    path('admin-panel/review/<int:pk>/',    views.admin_review_application,     name='review_application'),
    path('admin-panel/dashboard/',          views.admin_dashboard,              name='admin_dashboard'),
    path('admin/manage-users/',             views.admin_manage_users,           name='admin_manage_users'),
    path('admin/donor-list/',               views.admin_donor_list,             name='admin_donor_list'),
    path('admin/stats/',                    views.admin_stats,                  name='admin_stats'),
    path('admin-panel/requests/',           views.admin_request_queue,          name='admin_request_queue'),
    path('admin-panel/requests/<int:pk>/',  views.admin_review_request,         name='admin_review_request'),
    path('admin-panel/users/',              views.admin_user_list,              name='admin_user_list'),
    path('admin-panel/users/<int:pk>/',     views.admin_user_profile,           name='admin_user_profile'),

    # Donation tracking
    path('log-donation/',                   views.log_donation_view,            name='log_donation'),
    path('cooldown-status/',                views.cooldown_status_view,         name='cooldown_status'),

    # Notifications
    path('notifications/',                  views.notifications_page,           name='notifications_page'),
    path('notifications/read/',             views.mark_notifications_read,      name='mark_notifications_read'),
    path('notifications/<int:pk>/read/',    views.mark_single_notification_read,name='mark_single_notification_read'),
]