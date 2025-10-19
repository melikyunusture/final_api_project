from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
# Import RefreshToken inside the login_view to avoid static import resolution errors
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import UserSerializer, UserRegistrationSerializer

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    # import here to avoid unresolved import in some static analyzers/environments
    try:
        import importlib
        tokens_module = importlib.import_module('rest_framework_simplejwt.tokens')
        RefreshToken = getattr(tokens_module, 'RefreshToken')
    except Exception:
        return Response(
            {'error': 'RefreshToken import failed: install djangorestframework-simplejwt (pip install djangorestframework-simplejwt)'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    return Response(
        {'error': 'Invalid credentials'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )