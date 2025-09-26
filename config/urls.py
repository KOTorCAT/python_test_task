from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from core.web.views import SimpleHomeView, SimpleLoginView, SimpleRegisterView, SimpleProfileView
from core.web.views import SimpleProductsView, SimpleOrdersView, SimpleLogoutView
from core.api.views import HomePageView, LoginView, RegisterView, LogoutView, UserProfileView, UserDeleteView
from core.api.views import MockProductsView, MockOrdersView, AccessRuleListView, AccessRuleUpdateView

def root_redirect(request):
    return redirect('home_page')

urlpatterns = [
    # 🌐 WEB URLs (HTML - используют сессии Django)
    path('', root_redirect, name='root'),
    path('home/', SimpleHomeView.as_view(), name='home_page'),
    path('login/', SimpleLoginView.as_view(), name='simple_login'),
    path('register/', SimpleRegisterView.as_view(), name='simple_register'),
    path('profile/', SimpleProfileView.as_view(), name='simple_profile'),
    path('products/', SimpleProductsView.as_view(), name='simple_products'),
    path('orders/', SimpleOrdersView.as_view(), name='simple_orders'),
    path('logout/', SimpleLogoutView.as_view(), name='simple_logout'),
    
    # 🔌 API URLs (JSON - используют JWT токены)
    path('api/', HomePageView.as_view(), name='api_home'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/profile/', UserProfileView.as_view(), name='api_profile'),
    path('api/delete-account/', UserDeleteView.as_view(), name='api_delete_account'),
    path('api/products/', MockProductsView.as_view(), name='api_products'),
    path('api/orders/', MockOrdersView.as_view(), name='api_orders'),
    path('api/admin/access-rules/', AccessRuleListView.as_view(), name='api_access_rules_list'),
    path('api/admin/access-rules/<int:pk>/', AccessRuleUpdateView.as_view(), name='api_access_rules_update'),
    
    # ⚙️ АДМИНКА Django
    path('admin/', admin.site.urls),
]