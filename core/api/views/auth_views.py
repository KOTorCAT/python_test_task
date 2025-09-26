import jwt
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from core.models import User, Role

def create_jwt_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': timezone.now() + timezone.timedelta(days=1),
        'iat': timezone.now()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

class UserSerializer:
    def __init__(self, instance=None, data=None):
        self.instance = instance
        self.data = data
    
    def is_valid(self):
        if not self.data:
            return False
        required_fields = ['email', 'first_name', 'last_name']
        return all(field in self.data for field in required_fields)
    
    def save(self):
        if self.instance:
            for attr, value in self.data.items():
                setattr(self.instance, attr, value)
            self.instance.save()
            return self.instance
        else:
            return User.objects.create_user(**self.data)
    
    @property
    def errors(self):
        return {}

@permission_classes([AllowAny])
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Необходимо указать email, имя и фамилию'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.data.get('password') != request.data.get('password_confirm'):
            return Response(
                {'error': 'Пароли не совпадают'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_data = {
            'email': request.data['email'],
            'first_name': request.data['first_name'],
            'last_name': request.data['last_name'],
            'patronymic': request.data.get('patronymic', ''),
            'password': request.data['password']
        }
        
        user = User.objects.create_user(**user_data)
        user_role, _ = Role.objects.get_or_create(name='user')
        user.role = user_role
        user.save()
        
        token = create_jwt_token(user)
        return Response({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_201_CREATED)

@permission_classes([AllowAny])
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Необходимо указать email и пароль'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверные учетные данные'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {'error': 'Неверные учетные данные'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = create_jwt_token(user)
        return Response({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.name if user.role else None
            }
        })

class LogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Successfully logged out'})

class UserProfileView(APIView):
    def get(self, request):
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'patronymic': request.user.patronymic,
            'role': request.user.role.name if request.user.role else None
        })
    
    def put(self, request):
        serializer = UserSerializer(instance=request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'patronymic': request.user.patronymic
            })
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

class UserDeleteView(APIView):
    def post(self, request):
        request.user.delete()
        return Response({'message': 'Account deleted successfully'})

@permission_classes([AllowAny])
class HomePageView(APIView):
    def get(self, request):
        return Response({
            "message": "Добро пожаловать в систему аутентификации!",
            "api_endpoints": {
                "authentication": {
                    "login": "POST /api/login/",
                    "register": "POST /api/register/", 
                    "logout": "POST /api/logout/",
                    "profile": "GET /api/profile/",
                    "delete_account": "POST /api/delete-account/"
                },
                "business_objects": {
                    "products": "GET /api/products/",
                    "orders": "GET /api/orders/"
                },
                "admin": {
                    "access_rules": "GET /api/admin/access-rules/",
                    "update_rule": "PUT /api/admin/access-rules/{id}/"
                }
            },
            "documentation": "Используйте токен авторизации в заголовке: Authorization: Bearer <your_token>"
        })