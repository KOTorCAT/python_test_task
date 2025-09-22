import jwt
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import User, Role, BusinessElement, AccessRule

# ===== СЕРИАЛИЗАТОРЫ =====
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
            # Обновление
            for attr, value in self.data.items():
                setattr(self.instance, attr, value)
            self.instance.save()
            return self.instance
        else:
            # Создание
            return User.objects.create_user(**self.data)
    
    @property
    def errors(self):
        return {}

class LoginSerializer:
    def __init__(self, data=None):
        self.data = data
    
    def is_valid(self):
        if not self.data:
            return False
        return 'email' in self.data and 'password' in self.data
    
    @property
    def errors(self):
        return {}

class AccessRuleSerializer:
    def __init__(self, instance=None, data=None):
        self.instance = instance
        self.data = data
    
    def is_valid(self):
        return bool(self.data)
    
    def save(self):
        if self.instance:
            for attr, value in self.data.items():
                if hasattr(self.instance, attr):
                    setattr(self.instance, attr, value)
            self.instance.save()
            return self.instance
    
    @property
    def errors(self):
        return {}

# ===== КЛАССЫ РАЗРЕШЕНИЙ =====
class HasPermission:
    def __init__(self, element_name, action):
        self.element_name = element_name
        self.action = action
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            element = BusinessElement.objects.get(name=self.element_name)
            access_rule = AccessRule.objects.get(
                role=request.user.role, 
                element=element
            )
            
            permission_map = {
                'read': 'read_permission',
                'read_all': 'read_all_permission',
                'create': 'create_permission',
                'update': 'update_permission',
                'update_all': 'update_all_permission',
                'delete': 'delete_permission',
                'delete_all': 'delete_all_permission',
            }
            
            return getattr(access_rule, permission_map.get(self.action, 'read_permission'), False)
        except (BusinessElement.DoesNotExist, AccessRule.DoesNotExist):
            return False

def create_jwt_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': timezone.now() + timezone.timedelta(days=1),
        'iat': timezone.now()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# ===== API VIEWS =====
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
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Необходимо указать email и пароль'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = request.data['email']
        password = request.data['password']
        
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

class MockProductsView(APIView):
    def get(self, request):
        if not HasPermission('products', 'read').has_permission(request, self):
            return Response(
                {'error': 'Доступ запрещен'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        mock_products = [
            {'id': 1, 'name': 'Product 1', 'price': 100},
            {'id': 2, 'name': 'Product 2', 'price': 200},
            {'id': 3, 'name': 'Product 3', 'price': 300},
        ]
        return Response(mock_products)

class MockOrdersView(APIView):
    def get(self, request):
        if not HasPermission('orders', 'read').has_permission(request, self):
            return Response(
                {'error': 'Доступ запрещен'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        mock_orders = [
            {'id': 1, 'product': 'Product 1', 'status': 'completed'},
            {'id': 2, 'product': 'Product 2', 'status': 'pending'},
        ]
        return Response(mock_orders)

class AccessRuleListView(APIView):
    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {'error': 'Требуются права администратора'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        rules = AccessRule.objects.select_related('role', 'element').all()
        data = []
        for rule in rules:
            data.append({
                'id': rule.id,
                'role': rule.role.name,
                'element': rule.element.name,
                'permissions': {
                    'read': rule.read_permission,
                    'read_all': rule.read_all_permission,
                    'create': rule.create_permission,
                    'update': rule.update_permission,
                    'update_all': rule.update_all_permission,
                    'delete': rule.delete_permission,
                    'delete_all': rule.delete_all_permission,
                }
            })
        return Response(data)

class AccessRuleUpdateView(APIView):
    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response(
                {'error': 'Требуются права администратора'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            rule = AccessRule.objects.get(pk=pk)
        except AccessRule.DoesNotExist:
            return Response(
                {'error': 'Rule not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AccessRuleSerializer(instance=rule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Rule updated successfully'})
        
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

# ===== HTML VIEWS (для обычных пользователей) =====

class SimpleHomeView(TemplateView):
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        # Если пользователь уже авторизован - перенаправляем в профиль
        if request.user.is_authenticated:
            return redirect('simple_profile')
        return render(request, self.template_name)

@method_decorator(csrf_exempt, name='dispatch')
class SimpleLoginView(TemplateView):
    template_name = 'login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('simple_profile')
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email, is_active=True)
            if user.check_password(password):
                # Используем стандартную аутентификацию Django
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.first_name}!')
                return redirect('simple_profile')
            else:
                messages.error(request, 'Неверный пароль')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')
        
        return render(request, self.template_name)

@method_decorator(csrf_exempt, name='dispatch')
class SimpleRegisterView(TemplateView):
    template_name = 'register.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('simple_profile')
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic', '')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Валидация
        if not all([email, first_name, last_name, password, password_confirm]):
            messages.error(request, 'Все поля обязательны для заполнения')
            return render(request, self.template_name)
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name)
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, self.template_name)
        
        # Создание пользователя
        try:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                patronymic=patronymic,
                password=password
            )
            
            # Назначение роли "user" по умолчанию
            user_role, _ = Role.objects.get_or_create(name='user')
            user.role = user_role
            user.save()
            
            # Автоматический вход после регистрации
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, f'Регистрация успешна! Добро пожаловать, {user.first_name}!')
            return redirect('simple_profile')
            
        except Exception as e:
            messages.error(request, f'Ошибка при регистрации: {str(e)}')
            return render(request, self.template_name)

class SimpleProfileView(TemplateView):
    template_name = 'profile.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Для просмотра профиля необходимо войти в систему')
            return redirect('simple_login')
        
        context = {
            'user': request.user,
            'can_view_products': HasPermission('products', 'read').has_permission(request, self),
            'can_view_orders': HasPermission('orders', 'read').has_permission(request, self),
            'is_admin': request.user.is_superuser
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('simple_login')
        
        # Обновление профиля
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.patronymic = request.POST.get('patronymic', user.patronymic)
        user.save()
        
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('simple_profile')

class SimpleProductsView(TemplateView):
    template_name = 'products.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Для просмотра товаров необходимо войти в систему')
            return redirect('simple_login')
        
        # Проверка прав доступа
        if not HasPermission('products', 'read').has_permission(request, self):
            messages.error(request, 'У вас нет прав для просмотра товаров')
            return redirect('simple_profile')
        
        # Mock данные для отображения
        mock_products = [
            {'id': 1, 'name': 'Ноутбук игровой', 'price': 85000, 'description': 'Мощный ноутбук для игр и работы', 'category': 'Электроника'},
            {'id': 2, 'name': 'Смартфон', 'price': 45000, 'description': 'Флагманский смартфон', 'category': 'Электроника'},
            {'id': 3, 'name': 'Наушники беспроводные', 'price': 12000, 'description': 'Качественные наушники с шумоподавлением', 'category': 'Аксессуары'},
            {'id': 4, 'name': 'Клавиатура механическая', 'price': 8000, 'description': 'Игровая клавиатура с RGB подсветкой', 'category': 'Периферия'},
        ]
        
        context = {
            'products': mock_products,
            'user': request.user,
            'can_edit': HasPermission('products', 'update').has_permission(request, self)
        }
        return render(request, self.template_name, context)

class SimpleOrdersView(TemplateView):
    template_name = 'orders.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Для просмотра заказов необходимо войти в систему')
            return redirect('simple_login')
        
        # Проверка прав доступа
        if not HasPermission('orders', 'read').has_permission(request, self):
            messages.error(request, 'У вас нет прав для просмотра заказов')
            return redirect('simple_profile')
        
        # Mock данные для отображения
        mock_orders = [
            {'id': 1, 'product': 'Ноутбук игровой', 'status': 'доставлен', 'date': '2024-01-15', 'amount': 85000},
            {'id': 2, 'product': 'Смартфон', 'status': 'в обработке', 'date': '2024-01-16', 'amount': 45000},
            {'id': 3, 'product': 'Наушники беспроводные', 'status': 'отменен', 'date': '2024-01-10', 'amount': 12000},
        ]
        
        context = {
            'orders': mock_orders,
            'user': request.user,
            'can_manage': HasPermission('orders', 'update').has_permission(request, self)
        }
        return render(request, self.template_name, context)

class SimpleLogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'Вы вышли из системы')
        return redirect('home_page')

class SimpleDeleteAccountView(TemplateView):
    template_name = 'delete_account.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('simple_login')
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('simple_login')
        
        # Мягкое удаление аккаунта
        user = request.user
        user.delete()  # Это вызовет мягкое удаление (is_active=False)
        logout(request)
        
        messages.info(request, 'Ваш аккаунт был успешно удален')
        return redirect('home_page')
# 🔐 ADMIN VIEWS - Управление пользователями
class UserListView(TemplateView):
    template_name = 'admin_users.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            return redirect('home_page')
        
        users = User.objects.filter(is_active=True).select_related('role')
        context = {
            'users': users,
            'roles': Role.objects.all()
        }
        return render(request, self.template_name, context)

@method_decorator(csrf_exempt, name='dispatch')  # ← Добавьте этот декоратор
class UserUpdateView(TemplateView):
    template_name = 'admin_user_edit.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            return redirect('home_page')
        
        try:
            user = User.objects.get(pk=kwargs['pk'])
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден.')
            return redirect('user_list')
        
        context = {
            'edit_user': user,
            'roles': Role.objects.all()
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Доступ запрещен.')
            return redirect('home_page')
        
        try:
            user = User.objects.get(pk=kwargs['pk'])
            action = request.POST.get('action')
            
            if action == 'deactivate':
                # Деактивация пользователя
                user.is_active = False
                user.save()
                messages.success(request, f'Пользователь {user.email} деактивирован.')
                return redirect('user_list')
            
            # Изменение роли
            role_id = request.POST.get('role')
            if role_id:
                new_role = Role.objects.get(pk=role_id)
                user.role = new_role
                user.save()
                messages.success(request, f'Роль пользователя {user.email} обновлена.')
            else:
                messages.error(request, 'Роль не выбрана.')
                
        except (User.DoesNotExist, Role.DoesNotExist):
            messages.error(request, 'Ошибка обновления пользователя.')
        
        return redirect('user_list')

class UserManagementView(TemplateView):
    template_name = 'admin_user_management.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            return redirect('home_page')
        
        users = User.objects.filter(is_active=True).select_related('role')
        context = {
            'users': users,
            'roles': Role.objects.all()
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('home_page')
        
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(pk=user_id)
            
            if action == 'change_role':
                role_id = request.POST.get('role')
                if role_id:
                    new_role = Role.objects.get(pk=role_id)
                    user.role = new_role
                    user.save()
                    messages.success(request, f'Роль пользователя {user.email} изменена на {new_role.name}.')
            
            elif action == 'deactivate':
                user.is_active = False
                user.save()
                messages.success(request, f'Пользователь {user.email} деактивирован.')
            
            elif action == 'delete':
                user.delete()
                messages.success(request, f'Пользователь {user.email} удален.')
                
        except (User.DoesNotExist, Role.DoesNotExist):
            messages.error(request, 'Ошибка выполнения действия.')
        
        return redirect('user_management')