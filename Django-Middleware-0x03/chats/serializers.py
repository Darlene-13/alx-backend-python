# chats/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import User, Conversation, Message


# Get the User model (handles custom user models)
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    Handles user registration, profile updates, and user data display
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    full_name = serializers.SerializerMethodField()
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.CharField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'password', 'confirm_password',
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_full_name(self, obj):
        """Return the user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate_email(self, value):
        """Custom email validation"""
        if not value:
            raise serializers.ValidationError("Email is required")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def validate_username(self, value):
        """Custom username validation"""
        if not value:
            raise serializers.ValidationError("Username is required")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        return value

    def validate(self, attrs):
        """Validate password confirmation"""
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        # Create user with encrypted password
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Update user instance"""
        # Handle password update separately
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for nested relationships
    Returns minimal user information to avoid circular references
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['user_id', 'username', 'email', 'first_name', 'last_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model
    Handles message creation and display with sender information
    """
    sender = UserBasicSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    conversation_id = serializers.UUIDField(write_only=True)
    is_read = serializers.SerializerMethodField()
    time_since_sent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation_id',
            'message_body', 'message_type', 'file_url', 'sent_at',
            'is_read', 'time_since_sent'
        ]
        read_only_fields = ['message_id', 'sender', 'sent_at']

    def get_is_read(self, obj):
        """Check if message is read (placeholder for future implementation)"""
        # This would typically check against a read_receipts table
        return True

    def get_time_since_sent(self, obj):
        """Get human-readable time since message was sent"""
        
        now = timezone.now()
        diff = now - obj.sent_at
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"

    def create(self, validated_data):
        """Create a new message"""
        # Get sender from context (usually set in the view)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        
        return super().create(validated_data)

    def validate_message_body(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message body cannot be empty")
        if len(value) > 1000:
            raise serializers.ValidationError("Message is too long (max 1000 characters)")
        return value.strip()

    def validate_conversation_id(self, value):
        """Validate conversation exists"""
        try:
            conversation = Conversation.objects.get(conversation_id=value)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation does not exist")
        return value


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model
    Handles the many-to-many relationship with participants and nested messages
    """
    participants = UserBasicSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids', 'messages',
            'last_message', 'participant_count', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['conversation_id', 'participants', 'messages', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the most recent message in the conversation"""
        last_message = obj.messages.order_by('-sent_at').first()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'message_body': last_message.message_body[:50] + '...' if len(last_message.message_body) > 50 else last_message.message_body,
                'sender': last_message.sender.get_full_name(),
                'sent_at': last_message.sent_at,
                'message_type': last_message.message_type
            }
        return None

    def get_participant_count(self, obj):
        """Get the number of participants in the conversation"""
        return obj.participants.count()

    def get_unread_count(self, obj):
        """Get unread message count (placeholder for future implementation)"""
        # This would typically check against user's last_read timestamp
        return 0

    def create(self, validated_data):
        """Create a new conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        
        # Create the conversation
        conversation = Conversation.objects.create()
        
        # Add participants
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        # Add the creator to participants if not already included
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            conversation.participants.add(request.user)
        
        return conversation

    def update(self, instance, validated_data):
        """Update conversation participants"""
        participant_ids = validated_data.pop('participant_ids', None)
        
        if participant_ids is not None:
            participants = User.objects.filter(user_id__in=participant_ids)
            instance.participants.set(participants)
        
        return instance


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for conversation list views
    Excludes nested messages for better performance
    """
    participants = UserBasicSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'last_message',
            'participant_count', 'unread_count', 'updated_at'
        ]

    def get_last_message(self, obj):
        """Get the most recent message preview"""
        last_message = obj.messages.order_by('-sent_at').first()
        if last_message:
            return {
                'message_body': last_message.message_body[:100] + '...' if len(last_message.message_body) > 100 else last_message.message_body,
                'sender_name': last_message.sender.get_full_name(),
                'sent_at': last_message.sent_at,
                'message_type': last_message.message_type
            }
        return None

    def get_participant_count(self, obj):
        return obj.participants.count()

    def get_unread_count(self, obj):
        return 0  # Placeholder


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Specialized serializer for creating messages
    Simplified for message creation endpoints
    """
    conversation_id = serializers.UUIDField()
    
    class Meta:
        model = Message
        fields = ['conversation_id', 'message_body', 'message_type', 'file_url']

    def create(self, validated_data):
        """Create message with sender from request context"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        
        return super().create(validated_data)

    def validate_conversation_id(self, value):
        """Validate that conversation exists and user is a participant"""
        try:
            conversation = Conversation.objects.get(conversation_id=value)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation does not exist")
        
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if not conversation.participants.filter(user_id=request.user.user_id).exists():
                raise serializers.ValidationError("You are not a participant in this conversation")
        
        return value