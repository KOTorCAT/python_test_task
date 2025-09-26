import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Пропускаем для HTML страниц и admin (они используют сессии Django)
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/home/') or
            request.path.startswith('/login/') or
            request.path.startswith('/register/') or
            request.path.startswith('/profile/') or
            request.path.startswith('/products/') or
            request.path.startswith('/orders/') or
            not request.path.startswith('/api/')):
            return self.get_response(request)
        
        # Проверяем JWT только для API endpoints
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                user_id = payload.get('user_id')
                
                from core.models import User
                user = User.objects.filter(id=user_id, is_active=True).first()
                if user:
                    request.user = user
                else:
                    request.user = AnonymousUser()
                    
            except jwt.InvalidTokenError:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
        
        return self.get_response(request)