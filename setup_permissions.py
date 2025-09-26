import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Role, BusinessElement, AccessRule

def setup_permissions():
    print("=== Настройка прав доступа ===")
    
    # Получаем или создаем роли
    admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Администратор системы'})
    manager_role, _ = Role.objects.get_or_create(name='manager', defaults={'description': 'Менеджер'}) 
    user_role, _ = Role.objects.get_or_create(name='user', defaults={'description': 'Обычный пользователь'})
    
    print("✅ Роли созданы/найдены")
    
    # Бизнес-элементы (уже должны быть созданы ранее)
    elements_data = [
        {'name': 'users', 'description': 'Пользователи системы'},
        {'name': 'products', 'description': 'Товары'},
        {'name': 'orders', 'description': 'Заказы'},
        {'name': 'access_rules', 'description': 'Правила доступа'},
    ]
    
    elements = {}
    for element_data in elements_data:
        try:
            element = BusinessElement.objects.get(name=element_data['name'])
            elements[element_data['name']] = element
            print(f"✅ Найден бизнес-элемент: {element_data['name']}")
        except BusinessElement.DoesNotExist:
            # Если элемента нет - создаем
            element = BusinessElement.objects.create(**element_data)
            elements[element_data['name']] = element
            print(f"✅ Создан бизнес-элемент: {element_data['name']}")
    
    print("✅ Бизнес-элементы готовы")
    
    # Права для АДМИНА (все права на всё)
    for element_name, element in elements.items():
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
            print(f"✅ Настроены права админа для: {element_name}")
        else:
            print(f"⚠️ Права админа для {element_name} уже существуют")
    
    # Права для МЕНЕДЖЕРА
    manager_elements = ['products', 'orders']
    for element_name in manager_elements:
        rule, created = AccessRule.objects.get_or_create(
            role=manager_role,
            element=elements[element_name],
            defaults={
                'read_permission': True,
                'read_all_permission': True,
                'create_permission': True,
                'update_permission': True,
                'update_all_permission': True,
                'delete_permission': False,
                'delete_all_permission': False,
            }
        )
        if created:
            print(f"✅ Настроены права менеджера для: {element_name}")
        else:
            print(f"⚠️ Права менеджера для {element_name} уже существуют")
    
    # Права для ПОЛЬЗОВАТЕЛЯ (базовые)
    user_elements = ['products', 'orders']
    for element_name in user_elements:
        rule, created = AccessRule.objects.get_or_create(
            role=user_role,
            element=elements[element_name],
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
            print(f"✅ Настроены права пользователя для: {element_name}")
        else:
            print(f"⚠️ Права пользователя для {element_name} уже существуют")
    
    print("\n🎯 Система прав настроена!")
    print("👑 Admin - полный доступ ко всему")
    print("👔 Manager - управление товарами и заказами") 
    print("👤 User - просмотр товаров и заказов")
    print("\n💡 Теперь создайте пользователей и назначьте им роли через админку")

if __name__ == "__main__":
    setup_permissions()