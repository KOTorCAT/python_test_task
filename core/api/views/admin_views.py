from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import AccessRule, BusinessElement

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

class AccessRuleListView(APIView):
    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {'error': 'Требуются права администратора'}, 
                status=403
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
                status=403
            )
        
        try:
            rule = AccessRule.objects.get(pk=pk)
        except AccessRule.DoesNotExist:
            return Response(
                {'error': 'Rule not found'}, 
                status=404
            )
        
        serializer = AccessRuleSerializer(instance=rule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Rule updated successfully'})
        
        return Response({'error': 'Invalid data'}, status=400)