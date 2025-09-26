from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages

class SimpleProductsView(TemplateView):
    template_name = 'products.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Для просмотра товаров необходимо войти в систему')
            return redirect('simple_login')
        
        from core.api.views.business_views import HasPermission
        if not HasPermission('products', 'read').has_permission(request, self):
            messages.error(request, 'У вас нет прав для просмотра товаров')
            return redirect('simple_profile')
        
        mock_products = [
            {'id': 1, 'name': 'Ноутбук игровой', 'price': 85000, 'description': 'Мощный ноутбук для игр и работы', 'category': 'Электроника'},
            {'id': 2, 'name': 'Смартфон', 'price': 45000, 'description': 'Флагманский смартфон', 'category': 'Электроника'},
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
        
        from core.api.views.business_views import HasPermission
        if not HasPermission('orders', 'read').has_permission(request, self):
            messages.error(request, 'У вас нет прав для просмотра заказов')
            return redirect('simple_profile')
        
        mock_orders = [
            {'id': 1, 'product': 'Ноутбук игровой', 'status': 'доставлен', 'date': '2024-01-15', 'amount': 85000},
            {'id': 2, 'product': 'Смартфон', 'status': 'в обработке', 'date': '2024-01-16', 'amount': 45000},
        ]
        
        context = {
            'orders': mock_orders,
            'user': request.user,
            'can_manage': HasPermission('orders', 'update').has_permission(request, self)
        }
        return render(request, self.template_name, context)