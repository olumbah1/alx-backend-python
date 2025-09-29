from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification


class MessageModelTest(TestCase):
    """Test cases for Message model."""

    def setUp(self):
        """Set up test users."""
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """Test that a message can be created successfully."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is a test message!"
        )
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.timestamp)

    def test_message_str_representation(self):
        """Test the string representation of Message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        expected_str = f"Message from {self.sender.username} to {self.receiver.username}"
        self.assertIn(expected_str, str(message))

    def test_mark_as_read(self):
        """Test marking a message as read."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        self.assertFalse(message.is_read)
        message.mark_as_read()
        self.assertTrue(message.is_read)


class NotificationModelTest(TestCase):
    """Test cases for Notification model."""

    def setUp(self):
        """Set up test users and message."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message for notification"
        )

    def test_notification_creation(self):
        """Test that a notification can be created."""
        notification = Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="You have a new message"
        )
        
        self.assertEqual(notification.user, self.user2)
        self.assertEqual(notification.message, self.message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertFalse(notification.is_read)

    def test_notification_str_representation(self):
        """Test the string representation of Notification."""
        notification = Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="You have a new message from user1"
        )
        
        expected_str = f"Notification for {self.user2.username}:"
        self.assertIn(expected_str, str(notification))

    def test_mark_notification_as_read(self):
        """Test marking a notification as read."""
        notification = Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="Test notification"
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)

    def test_get_unread_count(self):
        """Test getting unread notification count."""
        # Create multiple notifications
        Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="Notification 1"
        )
        Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="Notification 2"
        )
        
        count = Notification.get_unread_count(self.user2)
        self.assertEqual(count, 2)

    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        # Create multiple notifications
        Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="Notification 1"
        )
        Notification.objects.create(
            user=self.user2,
            message=self.message,
            notification_type='message',
            content="Notification 2"
        )
        
        # Mark all as read
        Notification.mark_all_as_read(self.user2)
        
        # Check count
        count = Notification.get_unread_count(self.user2)
        self.assertEqual(count, 0)


class SignalTest(TestCase):
    """Test cases for signal functionality."""

    def setUp(self):
        """Set up test users."""
        self.sender = User.objects.create_user(
            username='signal_sender',
            email='sender@signal.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='signal_receiver',
            email='receiver@signal.com',
            password='testpass123'
        )

    def test_notification_created_on_message_save(self):
        """Test that a notification is automatically created when a message is saved."""
        # Count notifications before
        notification_count_before = Notification.objects.filter(user=self.receiver).count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="This should trigger a notification!"
        )
        
        # Count notifications after
        notification_count_after = Notification.objects.filter(user=self.receiver).count()
        
        # Assert notification was created
        self.assertEqual(notification_count_after, notification_count_before + 1)
        
        # Get the notification and verify details
        notification = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.content)
        self.assertFalse(notification.is_read)

    def test_notification_not_created_on_message_update(self):
        """Test that a notification is NOT created when a message is updated."""
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Count notifications
        notification_count = Notification.objects.filter(user=self.receiver).count()
        
        # Update the message
        message.content = "Updated content"
        message.save()
        
        # Count notifications again - should be the same
        notification_count_after = Notification.objects.filter(user=self.receiver).count()
        self.assertEqual(notification_count, notification_count_after)

    def test_multiple_messages_create_multiple_notifications(self):
        """Test that multiple messages create multiple notifications."""
        # Create multiple messages
        for i in range(3):
            Message.objects.create(
                sender=self.sender,
                receiver=self.receiver,
                content=f"Message number {i+1}"
            )
        
        # Check that 3 notifications were created
        notification_count = Notification.objects.filter(user=self.receiver).count()
        self.assertEqual(notification_count, 3)

    def test_notification_links_to_correct_message(self):
        """Test that each notification correctly links to its message."""
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message for linking"
        )
        
        # Get the notification
        notification = Notification.objects.get(
            user=self.receiver,
            message=message
        )
        
        # Verify the link
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.message.content, "Test message for linking")