from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/setup/', views.profile_setup_view, name='profile_setup'),
    path('', views.home_view, name='home'),
    path('switch-role/', views.switch_role_view, name='switch_role'),
]