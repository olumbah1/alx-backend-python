from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory

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
        self.assertFalse(message.edited)
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

    def test_message_edit_flag(self):
        """Test that editing a message sets the edited flag."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        self.assertFalse(message.edited)
        
        # Edit the message
        message.content = "Edited content"
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.edited_at)

    def test_get_edit_count(self):
        """Test getting the edit count of a message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        self.assertEqual(message.get_edit_count(), 0)
        
        # Edit the message multiple times
        message.content = "First edit"
        message.save()
        
        message.content = "Second edit"
        message.save()
        
        self.assertEqual(message.get_edit_count(), 2)


class MessageHistoryModelTest(TestCase):
    """Test cases for MessageHistory model."""

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
            content="Original message content"
        )

    def test_message_history_creation(self):
        """Test that message history can be created."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content",
            edited_by=self.user1
        )
        
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Old content")
        self.assertEqual(history.edited_by, self.user1)
        self.assertIsNotNone(history.edited_at)

    def test_message_history_str_representation(self):
        """Test the string representation of MessageHistory."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content",
            edited_by=self.user1
        )
        
        expected_str = f"Edit history for Message #{self.message.id}"
        self.assertIn(expected_str, str(history))

    def test_get_content_preview(self):
        """Test getting content preview from history."""
        long_content = "A" * 100
        history = MessageHistory.objects.create(
            message=self.message,
            old_content=long_content,
            edited_by=self.user1
        )
        
        preview = history.get_content_preview()
        self.assertEqual(len(preview), 53)  # 50 chars + "..."
        self.assertTrue(preview.endswith("..."))


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


class ThreadedMessageTest(TestCase):
    """Test cases for threaded message functionality."""

    def setUp(self):
        """Set up test users."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_create_root_message(self):
        """Test creating a root message without parent."""
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="This is a root message"
        )
        
        self.assertIsNone(message.parent_message)
        self.assertFalse(message.is_reply())
        self.assertEqual(message.get_thread_root(), message)

    def test_create_reply_message(self):
        """Test creating a reply to an existing message."""
        root_message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root message"
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="This is a reply",
            parent_message=root_message
        )
        
        self.assertEqual(reply.parent_message, root_message)
        self.assertTrue(reply.is_reply())
        self.assertEqual(reply.get_thread_root(), root_message)

    def test_nested_replies(self):
        """Test creating nested replies (reply to a reply)."""
        # Create root message
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root message"
        )
        
        # First level reply
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="First reply",
            parent_message=root
        )
        
        # Second level reply (reply to reply)
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Reply to reply",
            parent_message=reply1
        )
        
        # Verify hierarchy
        self.assertEqual(reply1.get_thread_root(), root)
        self.assertEqual(reply2.get_thread_root(), root)
        self.assertEqual(reply2.parent_message, reply1)

    def test_get_replies(self):
        """Test getting direct replies to a message."""
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root message"
        )
        
        # Create multiple replies
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1",
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 2",
            parent_message=root
        )
        
        replies = root.get_replies()
        self.assertEqual(replies.count(), 2)
        self.assertIn(reply1, replies)
        self.assertIn(reply2, replies)

    def test_get_all_replies_recursive(self):
        """Test getting all replies recursively including nested ones."""
        # Create a complex thread structure
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root"
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1",
            parent_message=root
        )
        
        reply1_1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Reply 1.1",
            parent_message=reply1
        )
        
        reply1_1_1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1.1.1",
            parent_message=reply1_1
        )
        
        reply2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 2",
            parent_message=root
        )
        
        # Get all replies recursively
        all_replies = root.get_all_replies_recursive()
        
        # Should include all 4 replies
        self.assertEqual(len(all_replies), 4)
        self.assertIn(reply1, all_replies)
        self.assertIn(reply1_1, all_replies)
        self.assertIn(reply1_1_1, all_replies)
        self.assertIn(reply2, all_replies)

    def test_get_reply_count(self):
        """Test getting the count of direct replies."""
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root"
        )
        
        self.assertEqual(root.get_reply_count(), 0)
        
        # Add direct replies
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1",
            parent_message=root
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 2",
            parent_message=root
        )
        
        self.assertEqual(root.get_reply_count(), 2)

    def test_get_total_reply_count(self):
        """Test getting total count of all replies including nested ones."""
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Root"
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply 1",
            parent_message=root
        )
        
        # Nested reply
        Message.objects.create(
            sender=self.user1,
            receiver=self.user)


class UnreadMessagesManagerTest(TestCase):
    """Test cases for custom UnreadMessagesManager."""

    def setUp(self):
        """Set up test users and messages."""
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_unread_for_user(self):
        """Test getting unread messages for a specific user."""
        # Create messages
        msg1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Unread message 1"
        )
        
        msg2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Unread message 2"
        )
        
        # Create a read message
        msg3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Read message",
            is_read=True
        )
        
        # Get unread messages using custom manager
        unread = Message.unread_messages.unread_for_user(self.user2)
        
        self.assertEqual(unread.count(), 2)
        self.assertIn(msg1, unread)
        self.assertIn(msg2, unread)
        self.assertNotIn(msg3, unread)

    def test_unread_count_for_user(self):
        """Test getting count of unread messages."""
        # Create unread messages
        for i in range(5):
            Message.objects.create(
                sender=self.user1,
                receiver=self.user2,
                content=f"Message {i}")