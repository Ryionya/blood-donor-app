from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',       admin.site.urls),
    path('',             include('accounts.urls')),       # register / login / logout / home
    path('recipients/',  include('recipients.urls')),     # browse / request / my-requests
    path('donors/',      include('donors.urls')),         # apply / dashboard (M2 / M4)
    path('webpush/',     include('webpush.urls')),        # M4 push notifications
    path('',             include('pwa.urls')),            # PWA manifest / sw
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
