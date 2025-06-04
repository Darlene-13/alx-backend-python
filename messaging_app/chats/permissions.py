from rest_framework import permissions
from .models import Conversation, Message


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to only access it
    """
    def has_permisssion(self, request, view):
        """
        Check if the user is authenticated
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant of the conversation
        """
        if isinstance(obj, Conversation):
            return obj.conversation.participants.filter(user_id = request.user.user_id).exists() # Checks if the user is a participants for conversation onbj
        elif isinstance(obj, Message):
            return obj.conversation.participants.filter(user_id=request.user.user_id).exists() # Checks if user is a participant for message objects
        return False
    

class IsMessageSenderOrParticipant(permissions.BasePermissions):
    """
    Custom permission to allow message sender or conversation participants to access messages
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request,obj,view):
        """
        Check for permissions based on actions
        Anyone can view messages if there are in the conversation
        Only sender can update/delete their own messages
        Participants can create new messages
        """

        if isinstance(obj, Message):
            # Check if user is a participant in the messages
            is_participant = obj.conversation.participants.filter(
                user_id = request.user.user_id
            ).exists()

            if not is_participant:
                return False
            
            # For safe methods (GET, HEAD, OPTIONS), allow all participants
            if request.method in permissions.SAFE_METHODS:
                return True
            
            # For destructive methods (PUT, PATCH, DELETE), only allow message sender
            if request.method in ['PUT, ''PATCH', 'DELETE']:
                return obj.sender.user_id == request.user.user_id
            
            # For POST (create), allow all participants
            return True
        
        return False
    
class IsOwnerOrReadOnly(permissions.BasePermissions):
    """
    Custom permission to only allow users of an object to edit it
    """
    def has_permission(sel, request, obj, view):
        """
        Check if user is authenticated
        """
        return request.use and request.user.is_authenticated
    
    def has_object_permission(self, request, obj, view):
        """
        Read permissions for any authenticated user
        Write permissions only to the owner of the object.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'sender'):
            return obj.sender == request.user
        elif hasattr(obj, 'participant'):
            return obj.participants.filter(user_id =request.user.user_id).exist()
        return False
    
class IsConversationParticipant(permissions.BasePermission):
    """
    Permission class to check if user is a participant in a conversation
    Used for nested routes like /comnversations/{id}/messages/
    """
    def has_permission(self,request, view):
        """
            Check if user is an authenticated participant
        """
        if not (request.user and request.user.is_authenticated):
            return False
        # Get conversation_pk from URL kwargs
        conversation_pk = view.kwargs.get('conversation_pk')
        if conversation_pk:
            try:
                conversation = Conversation.objects.get(conversation_id = conversation_pk)
                return conversation.participants.filter(
                    user_id=request.user.user_id
                ).exists()
            except Conversation.DoesNotExist:
                return False
        return True
    
    def has_object_permissions(self, request, view, obj):
        """
        Check object-level permissions
        """
        if isinstance(obj, Message):
            return obj.conversation.participants.filter(
                user_id = request.user.user_id
            ).exists()
        elif isinstance (obj, Conversation):
            return obj.participants.filter(
                user_id = request.user.user_id
            ).exists()
        return False
    
class CanCreateConversation(permissions.BasePermission):
    """
    Permission to allow authenticated user to create conversations
    """
    def has_permission(self, request, view):
        """
        Alllow authenticated users to create conversations
        """
        if request.method == 'POST':
            return request.user and request.user_is_authenticated
        return True
    
class CanSendMessage(permissions.BasePermission):
    """Allow conversation participants to send messages"""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method == 'POST':
            # Get conversation from request data or URL
            conversation_id = None

            # Try to get from URL Kwargs(nested route)
            conversation_pk = view.kwargs.get('conversation_pk')
            if conversation_pk:
                conversation_id = conversation_pk

            #Try to get from request data 
            elif hasattr(request, 'data') and 'conversation_id' in request.data:
                conversation_id = request.data.get('conversation_id')
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(conversation_id = conversation_id)
                    return conversation.participants.filter(
                        user_id = request.user.user_id
                    ).exists()
                except Conversation.DoesNotExist:
                    return False
        return True
    
# Combined permission classess for common use cases
class ConversationPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not( request.user and request.user.is_authenticated):
            return False
        
        # ALlow creation of authenticated users
        if request.method =='POST':
            return True
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Must be a participant of the conversation
        if isinstance(obj, Conversation):
            return obj.participants.filter(
                user_id=request.user.user_id
            ).exists()
        return False
    
class MessagePermissions(permissions.BasePermission):
    # Combined permission class for message endpoints
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # For creating messages, check conversation participation
        if request.method =='POST':
            conversation_pk = view.kwargs.get('conversation_pk')
            if conversation_pk:
                try:
                    conversation = Conversation.objects.get(conversation_id = conversation_pk)
                    return conversation.participnts.filter(
                        user_id = request.user.user_id
                    ).exists()
                except Conversation.DoesNotExist:
                    return False
            return True
        
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Message):
            # Mjst be a participant in the Conversation
            is_participant = obj.conversation.participants.filter(
                user_id = request.user.user_id
            ).exists()
            if not is_participant:
                return False
            
            # Read permissions for all participants
            if request.method in permissions.SAFE_METHODS:
                return True
            # Wrire permissions only 
            return obj.sender.user_id == request.user.user_id
        return False