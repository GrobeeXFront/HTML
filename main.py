import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.settings import settings  # Явный импорт
from modules.core.bot_manager import BotManager
from utils.logger import setup_logger

print(f"DEBUG: settings object: {dir(settings)}")  # Отладочная печать
print(f"DEBUG: TELEGRAM_TOKEN exists: {hasattr(settings, 'TELEGRAM_TOKEN')}")

async def main():
    # Настройка логирования с указанием имени
    logger = setup_logger(name="BotManager")
    
    try:
        logger.info("Starting Bot Manager initialization...")
        
        # Загрузка конфигурации
        bot = Bot(token=settings.TELEGRAM_TOKEN)
        dp = Dispatcher()
        
        # Инициализация ядра
        bot_manager = BotManager(bot=bot)
        
        # Регистрация обработчиков команд
        dp.include_router(bot_manager.router)
        
        logger.info("Bot Manager successfully initialized")
        logger.info("Starting polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Failed to start Bot Manager: {e}")
        raise
    finally:
        logger.info("Bot Manager shutdown")

if __name__ == "__main__":
    asyncio.run(main())
