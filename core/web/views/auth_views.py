from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from core.models import User, Role

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
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.first_name}!')
                return redirect('simple_profile')
            else:
                messages.error(request, 'Неверный пароль')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')
        
        return render(request, self.template_name)

class SimpleLogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'Вы вышли из системы')
        return redirect('home_page')

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
        
        if not all([email, first_name, last_name, password, password_confirm]):
            messages.error(request, 'Все поля обязательны для заполнения')
            return render(request, self.template_name)
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name)
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, self.template_name)
        
        try:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                patronymic=patronymic,
                password=password
            )
            
            user_role, _ = Role.objects.get_or_create(name='user')
            user.role = user_role
            user.save()
            
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
        
        from core.api.views.business_views import HasPermission
        context = {
            'user': request.user,
            'can_view_products': HasPermission('products', 'read').has_permission(request, self),
            'can_view_orders': HasPermission('orders', 'read').has_permission(request, self),
            'is_admin': request.user.is_superuser
        }
        return render(request, self.template_name, context)