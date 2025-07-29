from functools import wraps
from aiogram import types
from config.settings import settings  # Импортируем объект настроек

def check_access(level: str = "user"):
    """
    Декоратор для проверки прав доступа к командам бота
    
    Параметры:
        level (str): Требуемый уровень доступа ('admin' или 'user')
        
    Пример использования:
        @check_access(level='admin')
        async def admin_command(message: Message):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            # Проверка что сообщение от пользователя
            if not hasattr(message, 'from_user') or not message.from_user:
                await message.answer("⚠️ Ошибка: не удалось определить пользователя")
                return

            user_id = message.from_user.id
            
            # Проверка прав администратора
            if level == "admin":
                if not settings.ADMINS:  # Проверка что список админов не пустой
                    await message.answer("⚠️ Ошибка конфигурации: не заданы администраторы")
                    return
                
                if user_id not in settings.ADMINS:
                    await message.answer("🚫 Команда доступна только администраторам!")
                    return
            
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator