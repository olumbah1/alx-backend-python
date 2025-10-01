from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UnreadMessagesManager(models.Manager):
    """
    Custom manager to filter and retrieve unread messages for a user.
    Provides optimized queries with select_related, prefetch_related, and only().
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user.
        
        Args:
            user: User object
            
        Returns:
            QuerySet of unread messages
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get the count of unread messages for a user.
        
        Args:
            user: User object
            
        Returns:
            Integer count of unread messages
        """
        return self.filter(receiver=user, is_read=False).count()
    
    def unread_from_sender(self, receiver, sender):
        """
        Get unread messages from a specific sender to a receiver.
        
        Args:
            receiver: User who receives messages
            sender: User who sent messages
            
        Returns:
            QuerySet of unread messages
        """
        return self.filter(
            receiver=receiver,
            sender=sender,
            is_read=False
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def unread_threads_for_user(self, user):
        """
        Get all unread root messages (conversation threads) for a user.
        Only returns root messages without parents.
        
        Args:
            user: User object
            
        Returns:
            QuerySet of unread root messages
        """
        return self.filter(
            receiver=user,
            is_read=False,
            parent_message__isnull=True
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def unread_with_preview(self, user):
        """
        Get unread messages with only essential fields for preview.
        Uses .only() to optimize query by retrieving only necessary fields.
        
        Args:
            user: User object
            
        Returns:
            QuerySet with limited fields
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).select_related('sender').only(
            'id',
            'sender__username',
            'content',
            'timestamp',
            'is_read'
        ).order_by('-timestamp')
    
    def mark_all_as_read(self, user):
        """
        Mark all unread messages for a user as read.
        
        Args:
            user: User object
            
        Returns:
            Number of messages updated
        """
        return self.filter(receiver=user, is_read=False).update(is_read=True)
    
    def unread_by_conversation(self, user):
        """
        Get unread message count grouped by sender.
        Returns a dictionary with sender usernames and their unread message counts.
        
        Args:
            user: User object
            
        Returns:
            Dictionary {sender_username: count}
        """
        from django.db.models import Count
        
        unread_messages = self.filter(
            receiver=user,
            is_read=False
        ).values('sender__username').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {item['sender__username']: item['count'] for item in unread_messages}


class MessageQuerySet(models.QuerySet):
    """
    Custom QuerySet for Message model with additional filtering methods.
    """
    
    def unread(self):
        """Filter for unread messages only."""
        return self.filter(is_read=False)
    
    def read(self):
        """Filter for read messages only."""
        return self.filter(is_read=True)
    
    def for_user(self, user):
        """Filter messages where user is sender or receiver."""
        return self.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        )
    
    def received_by(self, user):
        """Filter messages received by user."""
        return self.filter(receiver=user)
    
    def sent_by(self, user):
        """Filter messages sent by user."""
        return self.filter(sender=user)
    
    def threads_only(self):
        """Filter for root messages only (no parent)."""
        return self.filter(parent_message__isnull=True)
    
    def replies_only(self):
        """Filter for reply messages only (has parent)."""
        return self.filter(parent_message__isnull=False)
    
    def optimized(self):
        """Apply standard optimizations with select_related."""
        return self.select_related('sender', 'receiver', 'parent_message')


class Message(models.Model):
    """
    Model representing a message sent between users.
    Supports threaded conversations with parent_message for replies.
    """
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
        help_text="Whether the message has been read by the receiver",
        db_index=True  # Add index for better query performance
    )
    edited = models.BooleanField(
        default=False,
        help_text="Whether the message has been edited"
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the message was last edited"
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent message if this is a reply"
    )

    # Default manager
    objects = MessageQuerySet.as_manager()
    
    # Custom manager for unread messages
    unread_messages = UnreadMessagesManager()

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['parent_message']),
            models.Index(fields=['receiver', 'is_read']),  # Composite index for unread queries
            models.Index(fields=['receiver', 'is_read', 'timestamp']),  # For sorting unread
        ]

    def __str__(self):
        read_status = "Read" if self.is_read else "Unread"
        edited_indicator = " (edited)" if self.edited else ""
        reply_indicator = f" [Reply to #{self.parent_message.id}]" if self.parent_message else ""
        return f"[{read_status}] Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}{edited_indicator}{reply_indicator}"

    def mark_as_read(self):
        """Mark this message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        """Mark this message as unread."""
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])

    def get_edit_history(self):
        """Get all edit history for this message."""
        return self.history.all().order_by('-edited_at')

    def get_edit_count(self):
        """Get the number of times this message has been edited."""
        return self.history.count()

    def is_reply(self):
        """Check if this message is a reply to another message."""
        return self.parent_message is not None

    def get_replies(self):
        """
        Get all direct replies to this message.
        Uses select_related to optimize queries.
        """
        return self.replies.select_related('sender', 'receiver').order_by('timestamp')

    def get_all_replies_recursive(self):
        """
        Recursively get all replies and their nested replies.
        Returns a flat list of all descendant messages.
        """
        replies = []
        for reply in self.get_replies():
            replies.append(reply)
            replies.extend(reply.get_all_replies_recursive())
        return replies

    def get_reply_count(self):
        """Get the total number of direct replies to this message."""
        return self.replies.count()

    def get_total_reply_count(self):
        """Get the total number of all replies (including nested replies)."""
        return len(self.get_all_replies_recursive())

    def get_thread_root(self):
        """
        Get the root message of this thread.
        If this message has no parent, it is the root.
        """
        if self.parent_message:
            return self.parent_message.get_thread_root()
        return self

    def get_thread_messages(self):
        """
        Get all messages in this thread (root + all replies).
        Optimized with select_related and prefetch_related.
        """
        root = self.get_thread_root()
        
        # Get all messages in thread using recursive query
        thread_messages = [root]
        thread_messages.extend(root.get_all_replies_recursive())
        
        return thread_messages

    def get_thread_participants(self):
        """Get all unique users participating in this thread."""
        thread_messages = self.get_thread_messages()
        participants = set()
        
        for message in thread_messages:
            participants.add(message.sender)
            participants.add(message.receiver)
        
        return list(participants)

    def get_unread_replies_count(self, user):
        """
        Get count of unread replies in this thread for a specific user.
        
        Args:
            user: User object
            
        Returns:
            Count of unread replies
        """
        return self.replies.filter(receiver=user, is_read=False).count()

    @classmethod
    def get_conversation_threads(cls, user1, user2):
        """
        Get all conversation threads between two users.
        Returns only root messages (messages without parent).
        Optimized query with prefetch_related.
        """
        return cls.objects.filter(
            parent_message__isnull=True
        ).filter(
            models.Q(sender=user1, receiver=user2) |
            models.Q(sender=user2, receiver=user1)
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('-timestamp')

    @classmethod
    def get_user_threads(cls, user):
        """
        Get all conversation threads involving a user.
        Returns only root messages with optimized queries.
        """
        return cls.objects.filter(
            parent_message__isnull=True
        ).filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('-timestamp')

    @classmethod
    def get_unread_inbox(cls, user, limit=None):
        """
        Get unread messages for user's inbox with optimized query.
        Uses custom manager and .only() for performance.
        
        Args:
            user: User object
            limit: Optional limit on number of messages
            
        Returns:
            QuerySet of unread messages
        """
        queryset = cls.unread_messages.unread_with_preview(user)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset

    @classmethod
    def get_inbox_summary(cls, user):
        """
        Get inbox summary with counts.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with inbox statistics
        """
        return {
            'total_received': cls.objects.filter(receiver=user).count(),
            'unread_count': cls.unread_messages.unread_count_for_user(user),
            'read_count': cls.objects.filter(receiver=user, is_read=True).count(),
            'unread_threads': cls.unread_messages.unread_threads_for_user(user).count(),
            'unread_by_sender': cls.unread_messages.unread_by_conversation(user),
        }


class MessageHistory(models.Model):
    """
    Model to store the history of message edits.
    Captures the old content before a message is updated.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The message this history entry belongs to"
    )
    old_content = models.TextField(
        help_text="Content of the message before the edit"
    )
    edited_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this edit was made"
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_edits',
        help_text="User who made the edit"
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
        indexes = [
            models.Index(fields=['-edited_at']),
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return f"Edit history for Message #{self.message.id} at {self.edited_at}"

    def get_content_preview(self):
        """Get a preview of the old content."""
        return f"{self.old_content[:50]}{'...' if len(self.old_content) > 50 else ''}"


class Notification(models.Model):
    """
    Model representing a notification for a user.
    Automatically created when a user receives a new message.
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('reply', 'New Reply'),
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
    """
    Model representing a message sent between users.
    Supports threaded conversations with parent_message for replies.
    """
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
    edited = models.BooleanField(
        default=False,
        help_text="Whether the message has been edited"
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the message was last edited"
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent message if this is a reply"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['parent_message']),
        ]

    def __str__(self):
        edited_indicator = " (edited)" if self.edited else ""
        reply_indicator = f" [Reply to #{self.parent_message.id}]" if self.parent_message else ""
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}{edited_indicator}{reply_indicator}"

    def mark_as_read(self):
        """Mark this message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def get_edit_history(self):
        """Get all edit history for this message."""
        return self.history.all().order_by('-edited_at')

    def get_edit_count(self):
        """Get the number of times this message has been edited."""
        return self.history.count()

    def is_reply(self):
        """Check if this message is a reply to another message."""
        return self.parent_message is not None

    def get_replies(self):
        """
        Get all direct replies to this message.
        Uses select_related to optimize queries.
        """
        return self.replies.select_related('sender', 'receiver').order_by('timestamp')

    def get_all_replies_recursive(self):
        """
        Recursively get all replies and their nested replies.
        Returns a flat list of all descendant messages.
        """
        replies = []
        for reply in self.get_replies():
            replies.append(reply)
            replies.extend(reply.get_all_replies_recursive())
        return replies

    def get_reply_count(self):
        """Get the total number of direct replies to this message."""
        return self.replies.count()

    def get_total_reply_count(self):
        """Get the total number of all replies (including nested replies)."""
        return len(self.get_all_replies_recursive())

    def get_thread_root(self):
        """
        Get the root message of this thread.
        If this message has no parent, it is the root.
        """
        if self.parent_message:
            return self.parent_message.get_thread_root()
        return self

    def get_thread_messages(self):
        """
        Get all messages in this thread (root + all replies).
        Optimized with select_related and prefetch_related.
        """
        root = self.get_thread_root()
        
        # Get all messages in thread using recursive query
        thread_messages = [root]
        thread_messages.extend(root.get_all_replies_recursive())
        
        return thread_messages

    def get_thread_participants(self):
        """Get all unique users participating in this thread."""
        thread_messages = self.get_thread_messages()
        participants = set()
        
        for message in thread_messages:
            participants.add(message.sender)
            participants.add(message.receiver)
        
        return list(participants)

    @classmethod
    def get_conversation_threads(cls, user1, user2):
        """
        Get all conversation threads between two users.
        Returns only root messages (messages without parent).
        Optimized query with prefetch_related.
        """
        return cls.objects.filter(
            parent_message__isnull=True
        ).filter(
            models.Q(sender=user1, receiver=user2) |
            models.Q(sender=user2, receiver=user1)
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('-timestamp')

    @classmethod
    def get_user_threads(cls, user):
        """
        Get all conversation threads involving a user.
        Returns only root messages with optimized queries.
        """
        return cls.objects.filter(
            parent_message__isnull=True
        ).filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('-timestamp')


class MessageHistory(models.Model):
    """
    Model to store the history of message edits.
    Captures the old content before a message is updated.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The message this history entry belongs to"
    )
    old_content = models.TextField(
        help_text="Content of the message before the edit"
    )
    edited_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this edit was made"
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_edits',
        help_text="User who made the edit"
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
        indexes = [
            models.Index(fields=['-edited_at']),
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return f"Edit history for Message #{self.message.id} at {self.edited_at}"

    def get_content_preview(self):
        """Get a preview of the old content."""
        return f"{self.old_content[:50]}{'...' if len(self.old_content) > 50 else ''}"


class Notification(models.Model):
    """
    Model representing a notification for a user.
    Automatically created when a user receives a new message.
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('reply', 'New Reply'),
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


class MessageHistory(models.Model):
    """
    Model to store the history of message edits.
    Captures the old content before a message is updated.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The message this history entry belongs to"
    )
    old_content = models.TextField(
        help_text="Content of the message before the edit"
    )
    edited_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this edit was made"
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_edits',
        help_text="User who made the edit"
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
        indexes = [
            models.Index(fields=['-edited_at']),
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return f"Edit history for Message #{self.message.id} at {self.edited_at}"

    def get_content_preview(self):
        """Get a preview of the old content."""
        return f"{self.old_content[:50]}{'...' if len(self.old_content) > 50 else ''}"


class Notification(models.Model):
    """
    Model representing a notification for a user.
    Automatically created when a user receives a new message.
    """
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


class Notification(models.Model):
    """
    Model representing a notification for a user.
    Automatically created when a user receives a new message.
    """
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