from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, Notification, MessageHistory


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal handler that logs the old content of a message before it's updated.
    Uses pre_save to capture the content before the edit is saved.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        **kwargs: Additional keyword arguments
    """
    # Check if this is an update (not a new message)
    if instance.pk:
        try:
            # Get the old message from database
            old_message = Message.objects.get(pk=instance.pk)
            
            # Check if content has changed
            if old_message.content != instance.content:
                # Create a history entry with the old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content,
                    edited_at=timezone.now(),
                    edited_by=instance.sender  # Assuming sender is the one editing
                )
                
                # Mark the message as edited
                instance.edited = True
                instance.edited_at = timezone.now()
                
                # Log for debugging
                print(f"📝 Message #{instance.pk} edited. Old content saved to history.")
                
        except Message.DoesNotExist:
            # This shouldn't happen, but handle it gracefully
            pass


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
    elif instance.edited:
        print(f"✏️ Message edited: #{instance.pk} by {instance.sender.username}")