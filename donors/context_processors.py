from .models import Notification
from django.utils import timezone
from donors.utils import send_notification

def notifications(request):
    if request.user.is_authenticated:
        if request.user.role == 'donor':
            try:
                profile = request.user.donor_profile
                if profile.is_verified and profile.verification_expires_at:
                    if timezone.now() >= profile.verification_expires_at:
                        profile.is_verified = False
                        profile.verified_at = None
                        profile.verification_expires_at = None
                        profile.save()

                        from donors.models import DonorApplication
                        DonorApplication.objects.filter(
                            donor=request.user,
                            status=DonorApplication.STATUS_APPROVED
                        ).update(status=DonorApplication.STATUS_UNVERIFIED)

                        send_notification(
                            user=request.user,
                            notif_type='rejected',
                            message='Your donor verification has expired (3 months). '
                                    'Please reapply to become a verified donor again.',
                        )
            except Exception as e:
                pass

        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:3]
        return {
            'unread_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_count': 0,
        'recent_notifications': [],
    }