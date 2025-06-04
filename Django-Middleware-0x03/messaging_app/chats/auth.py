from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framwork.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model

class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token Serializer that includes user information
    """
    @classmethod
    def get_tokens(cls,user):
        token = super().get_token(user)

        # Add custom claims
        token['user_id'] = str(user.user_id)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)


        #Add user information to the response
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data

        return data
    
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT Token Obtain View
    """
    serializer_class = CustomTokenObtainSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user and return JWT tokens
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate JWT Tokens for the new user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Add custom claims to access token
        access_token['user_id'] = str(user.user_id)
        access_token['email'] = user.email
        access_token['first_name'] = user.first_name
        access_token['lasy_name'] = user.last_name

        return Response({
            'user': UserSerializer(user).data,
            'access': str(access_token),
            'refresh': str(refresh),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user with email/password and return JWT tokens
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    #Authenticate user
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):

            # Generate JWT Tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Add custom claims
            access_token['user_id'] = str(user.user_id)
            access_token['email'] = user.email
            access_token['first_name'] = user.first_name
            access_token['last_name'] = user.last_name

            return Response({
                'user': UserSerializer(user).data,
                'access': str(access_token),
                'refresh': str(refresh),
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
    
        else:
            return Response({
                'eror': 'Invalid credentials'
            }, status= status.HTTP_401_UNAUTHORIZED
            )
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['POST'])
def logout_user(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'LogOut Successful'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def get_user_profile(request):
    """
    Get current user's profile information
    """
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status = status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view('PUT', 'PATCH')
def update_user_profile(request):
    """
    Update current user's profile information
    """
    if request.user_is_authenticated:
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=request.method =='PATCH'

        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)