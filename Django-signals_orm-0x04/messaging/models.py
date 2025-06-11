from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    """
    A model representing a message between users in the application.
    Fields: - sender: User who sends the message
            - receiver: User who receives the message
            - content: Text content of the message
            - timestamp: Time when the message was sent
    """
    sender = models.ForeignKey(User, on_delete= models.CASCADE, related_name='sent_messages', help_text='User who sent this message')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'received_messages', help_text='User who will receive this message')
    content = models.TextField(help_text='The message content')
    timestamp = models.DateTimeField(default = timezone.now, help_text= 'When the message was created')


    class Meta: 
        ordering = ['-timestamp'] # Most recent messages first
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}: {self.content[:50]}"
    
class Notification(models.Model):
    """
    A model represeting a notification for a user.
    Fields: - user: User who will receive the notification
            - message: The message that triggered the notification
            -content: The content of the notification
            -timestamp: When the notification was created
            - is_read: Boolean, indicating when the user read the notification
            """
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name='notifications', help_text= "User who will receive the notification")
    message = models.ForeignKey(Message, on_delte = models.CASCADE, related_name ='notifications',null=True, blank=True, help_text= "Message that triggered the notification")
    content = models.TextField(help_text= "The content of the notification")
    timestamp = models.DateTimeField(db_default= timezone.now, help_text= "When the notification was created")
    is_read = models.BooleanField(default=False, help_text= "Indicates if the notification has been read by the user")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f" Notification for {self.user.username}: {self.content[:50]}.....({status})"
    
    def mark_as_read(self):
        """
        Marks the notification as read.
        """
        self.is_read = True
        self.save()
