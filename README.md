# Система аутентификации и авторизации

## Быстрый запуск

```bash
# Установка
pip install -r requirements.txt

# База данных
python manage.py migrate
python setup_permissions.py
python create_test_users.py

# Запуск
python manage.py runserver
```

## Демо-аккаунт

```
Админ:     bread@mail.ru    / 123

```

## Основные URL

- **Главная:** http://127.0.0.1:8000/home/
- **Вход:** http://127.0.0.1:8000/login/
- **Регистрация:** http://127.0.0.1:8000/register/
- **Админка:** http://127.0.0.1:8000/admin/
- **API:** http://127.0.0.1:8000/api/

## Функциональность

### Аутентификация
- Регистрация (email, имя, фамилия, пароль)
- Вход по email/паролю
- Выход
- Мягкое удаление аккаунта (is_active=False)

### Авторизация
**Роли:**
- **Admin** - полный доступ
- **Manager** - управление товарами/заказами  
- **User** - просмотр товаров/заказами

**Права:** read, create, update, delete для каждого ресурса

### Ресурсы
- Пользователи (users)
- Товары (products) - mock данные
- Заказы (orders) - mock данные
- Правила доступа (access_rules)

## API Endpoints

```
POST    /api/register/     - регистрация
POST    /api/login/        - вход
POST    /api/logout/       - выход
GET     /api/profile/      - профиль
PUT     /api/profile/      - обновление профиля
POST    /api/delete-account/ - удаление аккаунта

GET     /api/products/     - товары (требуются права)
GET     /api/orders/       - заказы (требуются права)

GET     /api/admin/access-rules/     - правила доступа (только админ)
PUT     /api/admin/access-rules/{id}/ - изменение правил (только админ)
```

## Структура проекта

```
project/
├── config/           - настройки Django
├── core/            - основное приложение
│   ├── models.py    - модели User, Role, BusinessElement, AccessRule
│   ├── views.py     - API и HTML views
│   └── admin.py     - настройки админки
├── templates/       - HTML шаблоны
└── manage.py
```

## Для разработки

### Создание тестовых данных
```bash
python setup_permissions.py    # настраивает права
python create_test_users.py    # создает демо-пользователей
```

### Работа с пользователями через админку
http://127.0.0.1:8000/admin/core/user/

### Проверка прав
Ошибки:
- **401** - не авторизован
- **403** - нет прав доступа

## Технические детали

- **Кастомная модель User** (не стандартная Django)
- **JWT аутентификация** для API
- **Сессии Django** для браузера
- **Кастомные permissions** на основе ролей
- **Middleware** для автоматической аутентификации

Проект готов к использованию. Основная логика работает, интерфейс простой и функциональный.
