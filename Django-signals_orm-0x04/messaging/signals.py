from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification


@receiver(post_save, sender=Message)
def create_notification_on_new_message(sender, instance, created, **kwargs):
    """
    Signal handler that automatically creates a notification when a new message is sent.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Only create notification for new messages, not updates
    if created:
        # Create notification content
        notification_content = (
            f"You have a new message from {instance.sender.username}: "
            f"{instance.content[:50]}{'...' if len(instance.content) > 50 else ''}"
        )
        
        # Create the notification
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type='message',
            content=notification_content,
            timestamp=instance.timestamp
        )
        
        # Optional: Print for debugging (remove in production)
        print(f"✅ Notification created for {instance.receiver.username}")


@receiver(post_save, sender=Message)
def log_message_creation(sender, instance, created, **kwargs):
    """
    Signal handler that logs when a new message is created.
    
    This is a separate signal handler to demonstrate multiple handlers
    can listen to the same signal.
    """
    if created:
        print(f"📧 New message: {instance.sender.username} → {instance.receiver.username}")