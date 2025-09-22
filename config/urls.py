from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from core.views import (
    # API Views
    HomePageView,
    LoginView, 
    LogoutView, 
    RegisterView, 
    UserProfileView, 
    UserDeleteView,
    MockProductsView,
    MockOrdersView,
    AccessRuleListView,
    AccessRuleUpdateView,
    
    # HTML Views (новые - для простых пользователей)
    SimpleHomeView,
    SimpleLoginView,
    SimpleRegisterView,
    SimpleProfileView,
    SimpleProductsView,
    SimpleOrdersView,
    SimpleLogoutView,
    UserListView, 
    UserUpdateView, 
    UserManagementView
)

def root_redirect(request):
    """Перенаправление с корневого URL на главную страницу"""
    return redirect('home_page')

urlpatterns = [
    # 📍 Корневой URL - перенаправление на главную
    path('', root_redirect, name='root'),
    
    # 🏠 HTML СТРАНИЦЫ (для обычных пользователей)
    path('home/', SimpleHomeView.as_view(), name='home_page'),
    path('login/', SimpleLoginView.as_view(), name='simple_login'),
    path('register/', SimpleRegisterView.as_view(), name='simple_register'),
    path('profile/', SimpleProfileView.as_view(), name='simple_profile'),
    path('products/', SimpleProductsView.as_view(), name='simple_products'),
    path('orders/', SimpleOrdersView.as_view(), name='simple_orders'),
    path('logout/', SimpleLogoutView.as_view(), name='simple_logout'),
    
    # ⚙️ АДМИНКА Django
    path('admin/', admin.site.urls),
    
    # 🔐 API ENDPOINTS (для разработчиков/интеграций)
    path('api/', HomePageView.as_view(), name='api_home'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/profile/', UserProfileView.as_view(), name='profile'),
    path('api/delete-account/', UserDeleteView.as_view(), name='delete-account'),
    path('api/products/', MockProductsView.as_view(), name='products'),
    path('api/orders/', MockOrdersView.as_view(), name='orders'),
    path('api/admin/access-rules/', AccessRuleListView.as_view(), name='access-rules-list'),
    path('api/admin/access-rules/<int:pk>/', AccessRuleUpdateView.as_view(), name='access-rules-update'),
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('admin/users/manage/', UserManagementView.as_view(), name='user_management'),
]