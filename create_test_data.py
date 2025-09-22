import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Role, BusinessElement, AccessRule

def create_test_data():
    print("=== Заполнение базы тестовыми данными ===")
    
    # Создаем роли
    roles_data = [
        {'name': 'admin', 'description': 'Администратор системы'},
        {'name': 'manager', 'description': 'Менеджер'},
        {'name': 'user', 'description': 'Обычный пользователь'},
    ]
    
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(**role_data)
        if created:
            print(f"✅ Создана роль: {role.name}")
        else:
            print(f"⚠️ Роль уже существует: {role.name}")
    
    # Создаем бизнес-элементы
    elements_data = [
        {'name': 'users', 'description': 'Управление пользователями'},
        {'name': 'products', 'description': 'Товары'},
        {'name': 'orders', 'description': 'Заказы'},
        {'name': 'access_rules', 'description': 'Правила доступа'},
    ]
    
    for element_data in elements_data:
        element, created = BusinessElement.objects.get_or_create(**element_data)
        if created:
            print(f"✅ Создан бизнес-элемент: {element.name}")
        else:
            print(f"⚠️ Бизнес-элемент уже существует: {element.name}")
    
    # Создаем правила доступа для админа (все права)
    admin_role = Role.objects.get(name='admin')
    for element in BusinessElement.objects.all():
        rule, created = AccessRule.objects.get_or_create(
            role=admin_role,
            element=element,
            defaults={
                'read_permission': True,
                'read_all_permission': True,
                'create_permission': True,
                'update_permission': True,
                'update_all_permission': True,
                'delete_permission': True,
                'delete_all_permission': True,
            }
        )
        if created:
            print(f"✅ Созданы права админа для: {element.name}")
    
    # Создаем базовые права для обычного пользователя
    user_role = Role.objects.get(name='user')
    user_elements = ['products', 'orders']
    
    for element_name in user_elements:
        element = BusinessElement.objects.get(name=element_name)
        rule, created = AccessRule.objects.get_or_create(
            role=user_role,
            element=element,
            defaults={
                'read_permission': True,
                'read_all_permission': False,
                'create_permission': False,
                'update_permission': False,
                'update_all_permission': False,
                'delete_permission': False,
                'delete_all_permission': False,
            }
        )
        if created:
            print(f"✅ Созданы базовые права пользователя для: {element.name}")
    
    print("=== Заполнение завершено ===")
    print("\nДоступные роли:", list(Role.objects.values_list('name', flat=True)))
    print("Бизнес-элементы:", list(BusinessElement.objects.values_list('name', flat=True)))

if __name__ == "__main__":
    create_test_data()