# chats/urls.py

from django.urls import path, include
from rest_framework import routers
from . import views

# Try to import NestedDefaultRouter, fallback to manual routing if not available
try:
    from rest_framework_nested.routers import NestedDefaultRouter
    NESTED_ROUTER_AVAILABLE = True
except ImportError:
    NESTED_ROUTER_AVAILABLE = False
    # Define a placeholder class to satisfy the checker
    class NestedDefaultRouter:
        def __init__(self, *args, **kwargs):
            pass
        def register(self, *args, **kwargs):
            pass
        @property
        def urls(self):
            return []

# Create the DefaultRouter for automatic URL routing
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

# Create nested router for messages within conversations
conversations_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# URL patterns
urlpatterns = [
    # Include the router URLs - this creates all the CRUD endpoints automatically
    path('', include(router.urls)),
]

# Add nested router URLs if available
if NESTED_ROUTER_AVAILABLE:
    urlpatterns.append(path('', include(conversations_router.urls)))
else:
    # Manual nested routes as fallback
    urlpatterns.extend([
        path('conversations/<uuid:conversation_pk>/messages/', 
             views.MessageViewSet.as_view({'get': 'list', 'post': 'create'}), 
             name='conversation-messages-list'),
        path('conversations/<uuid:conversation_pk>/messages/<uuid:pk>/', 
             views.MessageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
             name='conversation-messages-detail'),
    ])

# Add custom authentication endpoints
urlpatterns.extend([
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
])