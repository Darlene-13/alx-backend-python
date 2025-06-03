# chats/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

# Create the main router for top-level resources
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

# Create nested router for messages within conversations  
conversations_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# URL patterns
urlpatterns = [
    # Include the main router URLs
    path('', include(router.urls)),
    
    # Include the nested router URLs  
    path('', include(conversations_router.urls)),
    
    # Custom authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
]