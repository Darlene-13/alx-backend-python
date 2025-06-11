from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from models import Message, Notification
from .signals import create_notification_for_new_message

class MessageModelTest(TestCase):
    """
    Test cases for the message model and its signals
    This class contains tests for the message model and the signal handlers
    that create notifications when a new message is created.
    It ensures that the signal handlers work correctly and that notifications
    are created as expected when a new message is saved.  
    """
    def setUp(self):
        # set up tests users for messaging tests
        self.sender = User.objects.create_user(
            username =  'sender',
            email = 'sender@example.com',
            password = 'testpass123'
        )
        self.receiver = User.objects.create_user(
            username = 'receiver',
            email = 'receiver@example.com',
            password = 'testpass123'
        )

    def test_message_creation(self):
        # This is a test message that can be created with all the required fields
        message = Message.objects.create(
            sender = self.sender,
            reciever = self.receiver,
            content = "Hello! This is a test message"
        )

        # Verfit all fields are set correctly
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, "Hello! This is a test message")
        self.assertTrue(message.timestamp)

    def test_message_str_representation(self):
        """
        Test the string representation of a message
        """
        message = Message.objects.create(
            sender =  self.sender,
            receiver = self.receiver,
            content = "This is a test message with some content to check in string representation"

        )

        expected_str = f"From {self.sender.username} to {self.receiver.username}: This is a test message with some content to chec"
        self.assertEqual(str(message), expected_str)

    def test_message_ordering(self):
        message1= Message.objects.create(
            sender = self.sender,
            receiver = self.receiver,
            content = "First message"
        )
        message2 = Message.objects.create(
            sender = self.sender,
            receiver = self.receiver,
            content = "Second message"
        )

        # Get all message and veryfy the ordering
        messages = list(Message.objects.all()) # This one creates a list of all the messages created and just to note we created all the messages with message.object.create thus to count them we use message.objects.all()
        # Veryfy that the messages are ordered by timestamp
        self.assertEqual(messages[0], message2)
        self.assertEqual(messages[1], message1)


class NotificationModelTest(TestCase):
    """
    Test cases for the notification model
    """
    def setUp(self):
        """ Set up test data for notification tests"""
        self.user = User.objects.create_user(
            username = 'testUser',
            email = 'test@example.com',
            password = 'testpass123'

        )
        self.sender = User.objects.create_user(
            username = 'testSender',
            email = 'sender@example.com',
            password = 'testpass123'
        )
        self.message = Message.objects.create(
            sender = self.sender,
            receiver = self.user,
            content = "Test message for notification"
        )

    def test_notification_creation(self):
        """Test that a notification can be created with all the required fields"""
        notification = Notification.objects.create(
            user = self.user,
            message = self.message,
            content = "You have a new message!"
        )


        # Verfiy that all fields are correctly set
        self.assertEqual(notification.user, self.user),
        self.assertEqual(notification.message, self.message),
        self.assertEqual(notification.content, "You have a new message!")
        self.assertFalse(notification.is_read) # DEfault should always be false unless the user has read the notification
        self.assertIsNotNone(notification.timestamp)   # Ensures that the timestamp is always set

    def test_notification_str_representation(self):
        notification = Notification.objects.create(
            useer = self.user,
            message = self.message,
            content = "This is a test notification with some longer content"
        )

        expected_str = f"Notification for {self.user.username}: This is a test notification with some longer content"
        self.assertEqual(str(notification), expected_str)

    def test_mark_as_read_method(self):
        """ Test the mark as read method in the notification model"""
        notification = Notification.objects.create(
            user = self.user, 
            message = self.message,
            content = "Test notification"
        )

        # Initially, should be unread 
        self.assertFalse(notification.is_read)

        # Mark as read 
        notification.mark_as_read()

        # Should now be read
        self.assertTrue(notification.is_read)


    def test_notification_without_message(self):
        """
        
        Test that notifications can be created without a message"""
        
        notification = Notification.objects.create(
            user = self.user,
            content= "This is a system notification"
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.content, "This is a system notification")

class  SignalTest(TestCase):
    """ Test cases for django signals functionality"""
    def setUp(self):
        """ set uptest test users for signal tests"""
        self.sender = User.objects.create_user(
            username = 'sender',
            email = 'Sender@example.com',
            password = 'testpass123'
        )

        self.receiver = User.objects.create_user(
            username = 'receiver',
            email = 'receiver@example.com',
            password = 'testpass123'
        )

    def test_signal_creates_notification_for_new_message(self):

        # Test that creating a new message automtically triggers a notification
        initial_notification_count = Notification.objects.count()

        message = Message.objects.create(
            sender = self.sender,
            receiver = self.receiver, 
            content = 'This message should trigger a notification'
        )

        # Check that exactly one notification was created
        final_notification_count = Notification.objects.count()
        self.assertEqual(final_notification_count, initial_notification_count + 1)

        # Get the created notification and verify its properties
        notification = Notification.objects.latest('timestamp')

        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertIn(self.sender.username, notification.content)
        self.assertIn(message.content[:50], notification.content)
        self.assertFalse(notification.is_read)

    def test_signal_does_not_trigger_on_message_update(self):
        """
        Test that updating an existing message does not trigger a notification
        """
        message = self.objects.create(
            sender = self.sender,
            receiver = self.receiver,
            content = "Updated message content"
        )

        # Count the notifications after the initial message creation
        initial_notification_count_after_creation = Notification.objects.count()

        # Update the message
        message.content = "Update message content"
        message.save()

        # Verify that no additional notification was created
        final_notification_count = Notification.objects.count()

        self.assertEqual(final_notification_count, initial_notification_count_after_creation)
        
    def test_multiple_messages_create_multiple_notifications(self):
        # Creat multiple message and verify that they create multiple notifications
        Message.objects.create(
            sender = self.sender,
            rceiver = self.receiver,
            content = "First message"
        )

        Message.objects.create(
            sender = self.sender,
            reciver = self.receiver,
            content = "Second message"
        )
        Message.objects.create(
            sender = self.sender, 
            receiver = self.receiver,
            content = "Third message"
        )

        #Verfity that 3 notifications were created
        final_count = Notification.objects.count()
        self.assertEqual(final_count, 3)


    def test_different_receiver_get_separate_notifications(self):
        # Create another receiver
        receiver2 = User.objects.create_user(
            username = "receiver2",
            email = "receiver2@example.com",
            passswoord = "testpass123"
        )

        # Send messages to both receivers
        message1 = Message.objects.create(
            sender = self.sender,
            receiver = self.receiver,
            content = "Message for receiver 1"
        )
        message2 = Message.objects.create(
            sender = self.sender,
            receiver = receiver2,
            content = "Message for receiver 2"
        )

        # Verify that each receiver got their message notification
        receiver1_notifications = Notification.objects.filter(user = self.receiver)
        receiver2_notifications = Notification.objects.filter(user = receiver2)

        self.assertEqual(receiver1_notifications.count(), 1)
        self.assertEqual(receiver2_notifications.count(), 1)

        # Verify that the correct there are cprrect message associations
        self.assertEqual(receiver1_notifications.first().message, message1)
        self.assertEqual(receiver2_notifications.first().message, message2)

class SignalDisconnectTest(TestCase):

    def setUp(self):
        """ Disconnect signals for isolated testing"""

        post_save.disconnect(create_notification_for_new_message, sender=Message)

        self.sender = User.objects.create_user(
            username = 'sender',
            email = 'sender@example.com',
            password = 'testpass123'

        )
        self.receiver = User.objects.create_user(
            username = 'receiver',
            email = 'receiver@example.com',
            password = 'testpass123'
        )

    def tearDown(self):
        """ Reconnect the signals after tests"""
        post_save.connect(create_notification_for_new_message, sender=Message)

    def test_message_creation_without_signals(self):
        # Test the messages can be created when signals are disconnected

        initial_notification_count = Notification.objects.count()

        # Create a new message
        message = Message.objects.create(
            sender = self.sender,
            receiver = self.receiver,
            content = " This ,essage should trigger notifications"
        )

        # Verify that the message was created
        self.assertIsNotNone(message.sender, self.sender)
        self.assertIsNotNone(message.receiver, self.receiver)

        # Verify that no notification was created
        final_notification_count = Notification.objects.count()
        self.assertEqual(final_notification_count, initial_notification_count)
