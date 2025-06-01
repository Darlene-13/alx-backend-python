from django.db import models

# Create your models here.

# messaging_app/chats/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Extended User model based on your USERS table schema.
    Extends Django's AbstractUser to match your database structure.
    """
    user_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the user"
    )
    first_name = models.CharField(
        max_length=150,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        help_text="User's last name"
    )
    email = models.EmailField(
        unique=True,
        help_text="User's email address"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User's phone number"
    )
    password_hash = models.CharField(
        max_length=255,
        help_text="Hashed password"
    )
    profile_picture = models.URLField(
        blank=True,
        null=True,
        help_text="URL to user's profile picture"
    )
    role = models.CharField(
        max_length=50,
        default='guest',
        choices=[
            ('guest', 'Guest'),
            ('host', 'Host'),
            ('admin', 'Admin')
        ],
        help_text="User's role in the system"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the user account was created"
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the user last logged in"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    
    class Meta:
        db_table = 'users'  # Match your database table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()


class Property(models.Model):
    """
    Property model based on your PROPERTY table schema.
    This is needed for the messaging context (users messaging about properties).
    """
    property_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    host_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hosted_properties'
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    max_guests = models.IntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        default='active',
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('pending', 'Pending')
        ]
    )
    
    class Meta:
        db_table = 'property'
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
    
    def __str__(self):
        return f"{self.name} in {self.city}"


class Booking(models.Model):
    """
    Booking model based on your BOOKINGS table schema.
    This provides context for messaging (users discussing bookings).
    """
    booking_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    property_id = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    guests_count = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ('completed', 'Completed')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"Booking {str(self.booking_id)[:8]} - {self.property_id.name}"


class Message(models.Model):
    """
    Message model based on your MESSAGES table schema.
    This matches exactly with your database structure.
    """
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the message"
    )
    conversation_id = models.UUIDField(
        help_text="Identifier for the conversation thread"
    )
    sender_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="The user who sent this message"
    )
    recipient_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="The user who received this message"
    )
    booking_id = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text="Related booking (if applicable)"
    )
    message_body = models.TextField(
        help_text="The content/text of the message"
    )
    read_status = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )
    read_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the message was read"
    )
    
    class Meta:
        db_table = 'messages'  # Match your database table name
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-sent_at']  # Most recent messages first
        indexes = [
            models.Index(fields=['conversation_id', '-sent_at']),
            models.Index(fields=['sender_id', '-sent_at']),
            models.Index(fields=['recipient_id', '-sent_at']),
        ]
    
    def __str__(self):
        content_preview = self.message_body[:50] + "..." if len(self.message_body) > 50 else self.message_body
        return f"{self.sender_id.get_full_name()}: {content_preview}"
    
    def mark_as_read(self):
        """Mark this message as read and set read_date."""
        if not self.read_status:
            self.read_status = True
            self.read_date = timezone.now()
            self.save(update_fields=['read_status', 'read_date'])
    
    def get_conversation_messages(self):
        """Get all messages in the same conversation."""
        return Message.objects.filter(
            conversation_id=self.conversation_id
        ).order_by('sent_at')
    
    @classmethod
    def get_conversation_between_users(cls, user1, user2, booking=None):
        """
        Get or create a conversation between two users.
        Returns the conversation_id.
        """
        # Look for existing conversation between these users
        existing_messages = cls.objects.filter(
            models.Q(sender_id=user1, recipient_id=user2) |
            models.Q(sender_id=user2, recipient_id=user1)
        )
        
        if booking:
            existing_messages = existing_messages.filter(booking_id=booking)
        
        existing_message = existing_messages.first()
        
        if existing_message:
            return existing_message.conversation_id
        else:
            # Generate new conversation ID
            return uuid.uuid4()
    
    @classmethod
    def create_message(cls, sender, recipient, message_body, booking=None):
        """
        Create a new message with proper conversation handling.
        """
        conversation_id = cls.get_conversation_between_users(
            sender, recipient, booking
        )
        
        return cls.objects.create(
            conversation_id=conversation_id,
            sender_id=sender,
            recipient_id=recipient,
            booking_id=booking,
            message_body=message_body
        )


# Additional utility model for conversation management
class Conversation(models.Model):
    """
    Virtual model to help manage conversations.
    This aggregates messages by conversation_id.
    """
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    participant_1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_1'
    )
    participant_2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_2'
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        unique_together = ['participant_1', 'participant_2', 'booking']
    
    def __str__(self):
        booking_info = f" (Booking: {self.booking.booking_id})" if self.booking else ""
        return f"Conversation: {self.participant_1.get_full_name()} & {self.participant_2.get_full_name()}{booking_info}"
    
    def get_messages(self):
        """Get all messages in this conversation."""
        return Message.objects.filter(
            conversation_id=self.conversation_id
        ).order_by('sent_at')
    
    def get_last_message(self):
        """Get the most recent message in this conversation."""
        return self.get_messages().last()
    
    def get_unread_count(self, user):
        """Get count of unread messages for a specific user."""
        return Message.objects.filter(
            conversation_id=self.conversation_id,
            recipient_id=user,
            read_status=False
        ).count()


# Model for saved properties/favorites (from your SAVED table)
class Saved(models.Model):
    """
    Model for saved/favorite properties based on your SAVED table schema.
    """
    saved_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_properties'
    )
    property_id = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='saved_by_users'
    )
    date_saved = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved'
        unique_together = ['user_id', 'property_id']
        verbose_name = 'Saved Property'
        verbose_name_plural = 'Saved Properties'
    
    def __str__(self):
        return f"{self.user_id.get_full_name()} saved {self.property_id.name}"