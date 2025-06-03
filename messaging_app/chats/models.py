from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid

# Create your models here.

class User(AbstractUser):
    """
    This is the custom user model extending django AbstractUser and additional fieids for the messaging_app
    """
    user_id = models.UUIDField(primary_key = True, default=uuid.uuid4,editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    # Use email as login field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() # Strip is meant to rmeove any leading whitespace
    
class Conversation(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations', blank=False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateField(auto_now_add= True)

    class Meta:
        db_table = 'conversations'
        verbose_name='Conversation'
        verbose_name_plural = 'Conversations'
        ordering= ['-updated_at']
    
    def __str__ (self):
        participant_names = [user.get_full_name() for user in self.participants.all()[:3]]
        if self.participants.count()> 3:
            participant_names.append(f"and {self.participants.count()-3} others")
        return f"Conversation: {','.join(participant_names)}"
    
    @property
    def last_message(self):
        """Get the most recent messages in the conversation"""
        return self.messages.order_by('-sent_at').first()
    
    def add_participants(self, user):
        """Add user to the conversation"""
        self.participants.add(user)
    
    def remove_participant(self, user):
        """Remove a user from the conversation"""
        self.participant.remove(user)
    def get_participant_count(self):
        """Get the number of participants in the conversation"""
        return self.participants.count()

class Message(models.Model):
    MESSAGES_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file','File'),
        ('audio', 'Audio'),
        ('video','Video'),
    ]

    message_id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_body = models.TextField(max_length=10, choices = MESSAGES_TYPE_CHOICES, default='text')
    file_url = models.URLField(blanlk=True, null=True)
    sent_at = models.DateTimeField(auto_add_now=True)

    class Meta:
        db_table = 'messages'
        verbose_name= 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Messafe from {self.sender.get_full_name()} in {self.conversation}"
    def is_text_message(self):
        return self.message_type =='text'
    
    def has_attachement(self):
        return bool(self.file_url)
    
# Signcal to update conversation when a new message is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender,instance, created, **kwargs):
    if created:
        instance.conversation.save(update_fields=['updated_at'])
        
    