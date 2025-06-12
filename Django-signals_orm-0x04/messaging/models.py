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
            - edited: Whether this message has been edited
            - last_edited: Timestamp for the last edit

    """
    sender = models.ForeignKey(User, on_delete= models.CASCADE, related_name='sent_messages', help_text='User who sent this message')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'received_messages', help_text='User who will receive this message')
    content = models.TextField(help_text='The message content')
    timestamp = models.DateTimeField(default = timezone.now, help_text= 'When the message was created')
    edited = models.BooleanField(default = False, help_text = "Whether this message was edited")
    last_edited = models.DateTimeField(null=True, blank=True, help_text= "When this message was edited")

    class Meta: 
        ordering = ['-timestamp'] # Most recent messages first
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        edited_indicator = " (edited)" if self.edited else ""
        return f"From {self.sender.username} to {self.receiver.username}: {self.content[:50]}    {edited_indicator}"
    
    def edi_message(self, new_content, editor = None):
        """
        Method to edite a message. This will trigger the pre_save signal
        to log the old content before updating it"""
        if editor and editor  !=self.sender:
            raise PermissionError(" Only the sender can edit the message")
        
        self.content = new_content
        self.edited = True
        self.last_edited = timezone.now()
        self.save()

    @property 
    def edit_count(self):
        """
        Return the number of times this message has been edited. """
        return self.history.count() if hasattr(self, 'history') else 0

class MessageHistory(models.Model):
    """Model to store history of the edits
    This model captures the old content before each edit
    Fields: -message: The message that was edited
            -old_content: The message content before the edit
            -edited_at : The timmestamp at which the message was edited
            -edited_by: The userb who edited the message
            -edit_reason: Optional reason for the edit
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name= 'history', help_text=" The mmessage that was edited")
    old_content = models.TextField(help_text= " The message content before the edit")
    edited_at = models.DateTimeField(default = timezone.now,help_text="When the edit occured")
    edit_reason = models.TextField(max_length= 200, null=True, blank =True, help_text=" Optional reason for edit")
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text= "User who edited the message")

    class Meta:
        ordering = ['-edited_at']
        verbose_name = "Message History"
        verbose_name_plural = "Message Histories"
        get_latest_by = 'edited_at'

    def __str__(self):
        return f" Edit of message {self.message_id} by {self.edited_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def content_preview(self):
        """ Returns a preview of the old content """
        return self.old_content[:100] + "...." if len(self.old_content) > 100 else self.old_content



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
        self.save(update_fields=['is_read'])
