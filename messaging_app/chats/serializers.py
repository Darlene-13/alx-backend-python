from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for Users
    """
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'profile_picture', 'is_online', 'last_seen',
            'created_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'last_seen']


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Messages
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'conversation', 'sender', 'sender_id', 
            'content', 'timestamp', 'is_read'
        ]
        read_only_fields = ['message_id', 'timestamp']
    
    def create(self, validated_data):
        # Set sender from request user if not provided
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversations - ensures nested relationships are handled properly,
    like including messages within a conversation
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids', 'messages',
            'is_group', 'group_name', 'created_by', 'created_at', 'updated_at',
            'last_message', 'unread_count', 'participant_count'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the most recent message in the conversation"""
        last_message = obj.messages.first()  # Already ordered by -timestamp
        if last_message:
            return {
                'message_id': last_message.message_id,
                'content': last_message.content,
                'sender': last_message.sender.username,
                'timestamp': last_message.timestamp,
                'is_read': last_message.is_read
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0
    
    def get_participant_count(self, obj):
        """Get number of participants in conversation"""
        return obj.participants.count()
    
    def create(self, validated_data):
        """Create conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        request = self.context.get('request')
        
        # Set created_by to current user
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        # Add current user as participant if not already included
        if request and request.user.is_authenticated:
            conversation.participants.add(request.user)
        
        return conversation
