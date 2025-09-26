from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import BusinessElement, AccessRule

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

class MockProductsView(APIView):
    def get(self, request):
        if not HasPermission('products', 'read').has_permission(request, self):
            return Response(
                {'error': 'Доступ запрещен'}, 
                status=403
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
                status=403
            )
        
        mock_orders = [
            {'id': 1, 'product': 'Product 1', 'status': 'completed'},
            {'id': 2, 'product': 'Product 2', 'status': 'pending'},
        ]
        return Response(mock_orders)