from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent the message"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="User who receives the message"
    )
    content = models.TextField(
        help_text="Content of the message"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the message was sent"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read by the receiver"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['sender', 'receiver']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}"

    def mark_as_read(self):
        """Mark this message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('alert', 'Alert'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives the notification"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Related message if notification is about a message"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='message',
        help_text="Type of notification"
    )
    content = models.TextField(
        help_text="Notification content/message"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the notification was created"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.content[:50]}"

    def mark_as_read(self):
        """Mark this notification as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def get_unread_count(cls, user):
        """Get the count of unread notifications for a user."""
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a specific user."""
        return cls.objects.filter(user=user, is_read=False).update(is_read=True)