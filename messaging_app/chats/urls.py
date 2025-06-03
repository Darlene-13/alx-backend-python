# chats/urls.py

from django.urls import path, include
from rest_framework import routers
from . import views

# Create the DefaultRouter for automatic URL routing
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

# URL patterns
urlpatterns = [
    # Include the router URLs - this creates all the CRUD endpoints automatically
    path('', include(router.urls)),
    
    # Custom nested routes for messages within conversations
    path('conversations/<uuid:conversation_pk>/messages/', 
         views.MessageViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='conversation-messages-list'),
    path('conversations/<uuid:conversation_pk>/messages/<uuid:pk>/', 
         views.MessageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='conversation-messages-detail'),
    
    # Custom authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
]