from .models import Notification

def send_notification(user, notif_type, message):
    Notification.objects.create(
        user=user,
        notif_type=notif_type,
        message=message,
    )