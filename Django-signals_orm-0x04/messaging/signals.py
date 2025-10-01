from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
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


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler that cleans up all related data when a user is deleted.
    
    This handles deletion of:
    - Messages sent by the user
    - Messages received by the user
    - Notifications for the user
    - Message histories associated with the user
    
    Args:
        sender: The model class (User)
        instance: The User instance being deleted
        **kwargs: Additional keyword arguments
    """
    username = instance.username
    
    print(f"🗑️  Post-delete signal triggered for user: {username}")
    
    # Count items before deletion (for logging)
    sent_messages_count = Message.objects.filter(sender=instance).count()
    received_messages_count = Message.objects.filter(receiver=instance).count()
    notifications_count = Notification.objects.filter(user=instance).count()
    message_edits_count = MessageHistory.objects.filter(edited_by=instance).count()
    
    print(f"   📊 Data to be cleaned up:")
    print(f"      - Sent messages: {sent_messages_count}")
    print(f"      - Received messages: {received_messages_count}")
    print(f"      - Notifications: {notifications_count}")
    print(f"      - Message edits: {message_edits_count}")
    
    # Delete messages sent by the user
    # (CASCADE on ForeignKey should handle this, but we can be explicit)
    deleted_sent = Message.objects.filter(sender=instance).delete()
    print(f"   ✅ Deleted sent messages: {deleted_sent[0] if deleted_sent[0] else 0}")
    
    # Delete messages received by the user
    deleted_received = Message.objects.filter(receiver=instance).delete()
    print(f"   ✅ Deleted received messages: {deleted_received[0] if deleted_received[0] else 0}")
    
    # Delete notifications for the user
    deleted_notifications = Notification.objects.filter(user=instance).delete()
    print(f"   ✅ Deleted notifications: {deleted_notifications[0] if deleted_notifications[0] else 0}")
    
    # Update message histories where user was the editor (set to NULL)
    # This preserves the history but removes the user reference
    updated_histories = MessageHistory.objects.filter(edited_by=instance).update(edited_by=None)
    print(f"   ✅ Updated message histories: {updated_histories}")
    
    print(f"✅ User cleanup completed for: {username}")


@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """
    Signal handler that logs when user data is changed.
    
    This is useful for auditing purposes.
    
    Args:
        sender: The model class (User)
        instance: The User instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            
            # Check if username changed
            if old_user.username != instance.username:
                print(f"⚠️  Username changed: {old_user.username} → {instance.username}")
            
            # Check if email changed
            if old_user.email != instance.email:
                print(f"📧 Email changed for {instance.username}: {old_user.email} → {instance.email}")
                
        except User.DoesNotExist:
            pass
    else:
        # New user being created
        print(f"👤 New user being created: {instance.username}")