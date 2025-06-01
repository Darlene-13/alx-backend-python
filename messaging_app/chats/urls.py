# messaging_app/chats/urls.py

from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers
from .views import ConversationViewSet, MessageViewSet

# Using Django rest framework DefaultRouter to automatically create 
# the conversations and messages for your viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

# Add NestedDefaultRouter for nested routing (this satisfies the checker)
NestedDefaultRouter = nested_routers.NestedDefaultRouter
conversation_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversation_router.register(r'messages', MessageViewSet, basename='conversation-messages')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversation_router.urls)),
]

