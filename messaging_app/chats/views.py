# ===================================================================
# FIX 1: chats/views.py - Add "filters" to address the first check
# ===================================================================

# messaging_app/chats/views.py

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    Create viewsets for listing conversations - Using viewsets from rest-framework
    Implement the endpoints to create a new conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_group', 'created_at']
    search_fields = ['group_name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Return conversations for the current user"""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages').annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')
    
    def create(self, request, *args, **kwargs):
        """
        Implement the endpoints to create a new conversation
        POST /api/conversations/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the conversation
        conversation = serializer.save()
        
        # Return the created conversation with full details
        response_serializer = ConversationSerializer(
            conversation, 
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """
        List conversations for the authenticated user
        GET /api/conversations/
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get a specific conversation with all messages
        GET /api/conversations/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Add a participant to the conversation
        POST /api/conversations/{id}/add_participant/
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
            conversation.participants.add(user)
            return Response({
                'status': 'success',
                'message': f'User {user.username} added to conversation'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """
        Remove a participant from the conversation
        POST /api/conversations/{id}/remove_participant/
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
            conversation.participants.remove(user)
            return Response({
                'status': 'success',
                'message': f'User {user.username} removed from conversation'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    Create viewsets for listing messages - Using viewsets from rest-framework
    Implement the endpoints to send messages to an existing one
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_read', 'timestamp']
    search_fields = ['content']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Return messages for conversations the user is part of"""
        user_conversations = Conversation.objects.filter(
            participants=self.request.user
        )
        return Message.objects.filter(
            conversation__in=user_conversations
        ).select_related('sender', 'conversation').order_by('-timestamp')
    
    def create(self, request, *args, **kwargs):
        """
        Implement the endpoints to send messages to an existing conversation
        POST /api/messages/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the conversation ID from request data
        conversation_id = request.data.get('conversation')
        if not conversation_id:
            return Response(
                {'error': 'conversation field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user is participant in the conversation
        try:
            conversation = Conversation.objects.get(
                conversation_id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message with the authenticated user as sender
        message = serializer.save(sender=request.user)
        
        # Return the created message with full details
        response_serializer = MessageSerializer(
            message, 
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Get messages by conversation ID
        GET /api/messages/by_conversation/?conversation_id={uuid}
        """
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify user is participant in the conversation
            conversation = Conversation.objects.get(
                conversation_id=conversation_id,
                participants=request.user
            )
            
            # Get messages in chronological order for chat display
            messages = Message.objects.filter(
                conversation=conversation
            ).select_related('sender').order_by('timestamp')
            
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'}, 
                status=status.HTTP_404_NOT_FOUND
            )


# ===================================================================
# FIX 2: chats/urls.py - Add "routers.DefaultRouter()" to address second check
# ===================================================================

# messaging_app/chats/urls.py

from django.urls import path, include
from rest_framework import routers
from .views import ConversationViewSet, MessageViewSet

# Using Django rest framework DefaultRouter to automatically create 
# the conversations and messages for your viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]


# ===================================================================
# FIX 3: messaging_app/urls.py - Add "api/" to address third check
# ===================================================================

# messaging_app/urls.py

"""
URL configuration for messaging_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chats.urls')),  # Include chats app URLs with 'api' prefix
    path('api-auth/', include('rest_framework.urls')),  # DRF authentication URLs
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ===================================================================
# COMPLETE MODELS FILE FOR REFERENCE
# ===================================================================

# messaging_app/chats/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Extended User model - extension of AbstractUser for values not defined in built-in User model
    """
    user_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats_user'
        
    def __str__(self):
        return f"{self.username} ({self.email})"


class Conversation(models.Model):
    """
    Create the conversation model that tracks which users are involved in a conversation
    """
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats_conversation'
        ordering = ['-updated_at']
        
    def __str__(self):
        if self.is_group and self.group_name:
            return f"Group: {self.group_name}"
        participants = self.participants.all()[:2]
        if participants:
            return f"Conversation: {' & '.join([p.username for p in participants])}"
        return f"Conversation {str(self.conversation_id)[:8]}"


class Message(models.Model):
    """
    Message model containing the sender, conversation as defined in the shared schema
    """
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'chats_message'
        ordering = ['-timestamp']
        
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.sender.username}: {content_preview}"


# ===================================================================
# COMPLETE SERIALIZERS FILE FOR REFERENCE
# ===================================================================

# messaging_app/chats/serializers.py

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