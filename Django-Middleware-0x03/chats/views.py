# chats/views.py

from rest_framework import viewsets, status, permissions, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import User, Conversation, Message
from .serializers import (
    UserSerializer, 
    ConversationSerializer, 
    ConversationListSerializer,
    MessageSerializer,
    MessageCreateSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Allow registration without authentication
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations
    Provides endpoints for listing, creating, updating, and deleting conversations
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['participants__first_name', 'participants__last_name', 'participants__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """
        Return conversations where the user is a participant
        Filter conversations to only show those the authenticated user is part of
        """
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages')
    
    def get_serializer_class(self):
        """
        Use different serializers for list vs detail views
        ConversationListSerializer for better performance in list view
        """
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new conversation
        Endpoint: POST /api/conversations/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the conversation
        conversation = serializer.save()
        
        # Add the current user as a participant if not already added
        if not conversation.participants.filter(user_id=request.user.user_id).exists():
            conversation.participants.add(request.user)
        
        # Return the created conversation
        response_serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """
        Add the current user as a participant when creating a conversation
        """
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Add a participant to an existing conversation
        Endpoint: POST /api/conversations/{id}/add_participant/
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(user_id=user_id)
            conversation.participants.add(user)
            return Response({
                'message': f'User {user.get_full_name()} added to conversation'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """
        Remove a participant from an existing conversation
        Endpoint: POST /api/conversations/{id}/remove_participant/
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(user_id=user_id)
            conversation.participants.remove(user)
            return Response({
                'message': f'User {user.get_full_name()} removed from conversation'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations
    Provides endpoints for listing, creating, updating, and deleting messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message_body', 'sender__first_name', 'sender__last_name']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        """
        Return messages for a specific conversation where user is a participant
        Filters messages to only show those from conversations the user is part of
        """
        conversation_pk = self.kwargs.get('conversation_pk')
        if conversation_pk:
            # For nested routes (/conversations/{id}/messages/)
            return Message.objects.filter(
                conversation_id=conversation_pk,
                conversation__participants=self.request.user
            ).select_related('sender', 'conversation')
        else:
            # For direct message access (/messages/)
            return Message.objects.filter(
                conversation__participants=self.request.user
            ).select_related('sender', 'conversation')
    
    def get_serializer_class(self):
        """
        Use different serializers for create vs other actions
        MessageCreateSerializer for simplified message creation
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new message and send it to an existing conversation
        Endpoint: POST /api/conversations/{conversation_id}/messages/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get conversation from URL or request data
        conversation_pk = self.kwargs.get('conversation_pk')
        if conversation_pk:
            conversation_id = conversation_pk
        else:
            conversation_id = request.data.get('conversation_id')
        
        # Verify conversation exists and user is participant
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
            if not conversation.participants.filter(user_id=request.user.user_id).exists():
                return Response({
                    'error': 'You are not a participant in this conversation'
                }, status=status.HTTP_403_FORBIDDEN)
        except Conversation.DoesNotExist:
            return Response({
                'error': 'Conversation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create the message
        message = serializer.save(
            sender=request.user,
            conversation=conversation
        )
        
        # Return the created message with full details
        response_serializer = MessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """
        Set the sender to the current user and conversation from URL
        """
        conversation_pk = self.kwargs.get('conversation_pk')
        if conversation_pk:
            try:
                conversation = Conversation.objects.get(conversation_id=conversation_pk)
                serializer.save(
                    sender=self.request.user,
                    conversation=conversation
                )
            except Conversation.DoesNotExist:
                raise serializers.ValidationError("Conversation not found")
        else:
            serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        """
        Get all messages sent by the current user
        Endpoint: GET /api/messages/my_messages/
        """
        messages = Message.objects.filter(
            sender=request.user,
            conversation__participants=request.user
        ).order_by('-sent_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get unread messages for the current user (placeholder implementation)
        Endpoint: GET /api/messages/unread/
        """
        # This is a placeholder - in a real app, you'd track read status
        messages = Message.objects.filter(
            conversation__participants=request.user
        ).exclude(sender=request.user).order_by('-sent_at')[:20]
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class RegisterView(APIView):
    """
    User registration endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    """
    User login endpoint that returns token
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    User logout endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out'}, 
                          status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Something went wrong'}, 
                          status=status.HTTP_400_BAD_REQUEST)