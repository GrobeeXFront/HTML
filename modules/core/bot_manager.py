from aiogram import Router, types, F  # Добавляем F
from aiogram.filters import Command  # Удаляем Text
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dataclasses import dataclass
from typing import Dict, Optional
import re
from config import settings
from config.bots_config import BotConfig, BotConfigManager
from modules.linux.ssh import SSHManager
from modules.core.auth import check_access

router = Router()

# --- Классы состояний ---
class AddBotStates(StatesGroup):
    WAITING_NAME = State()
    WAITING_IP = State()
    WAITING_CREDENTIALS = State()
    WAITING_PATH = State()
    WAITING_GIT = State()
    CONFIRMATION = State()

# --- Вспомогательные классы ---
@dataclass
class ManagedBot:
    config: BotConfig
    status: str = "unknown"

# --- Валидация ---
def validate_ip(ip: str) -> bool:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    return re.match(pattern, ip) is not None

def validate_git(url: str) -> bool:
    pattern = r"^(https?|git)://.+\.git$"
    return re.match(pattern, url) is not None

# --- Основной класс ---
class BotManager:
    def __init__(self, bot):
        self.bot = bot
        self.router = Router()
        self.ssh = SSHManager()
        self.bots: Dict[str, ManagedBot] = self._load_bots()
        self._register_handlers()

    def _load_bots(self) -> Dict[str, ManagedBot]:
        """Загрузка ботов из конфига"""
        return {
            name: ManagedBot(config=config)
            for name, config in BotConfigManager.load().items()
        }

    def _register_handlers(self):
        # Команды управления
        self.router.message(Command("start"))(self.start_handler)
        self.router.message(Command("list_bots"))(self.list_bots_handler)
        self.router.message(Command("add_bot"))(self.add_bot_start)
        self.router.message(Command("cancel"))(self.cancel_handler)
        
        # Обработчики состояний
        self.router.message(AddBotStates.WAITING_NAME)(self.handle_name)
        self.router.message(AddBotStates.WAITING_IP)(self.handle_ip)
        self.router.message(AddBotStates.WAITING_CREDENTIALS)(self.handle_credentials)
        self.router.message(AddBotStates.WAITING_PATH)(self.handle_path)
        self.router.message(AddBotStates.WAITING_GIT)(self.handle_git)
        self.router.message(AddBotStates.CONFIRMATION)(self.handle_confirmation)

    # --- Основные команды ---
    @check_access(level="user")
    async def start_handler(self, message: Message):
        await message.answer(
            "🤖 Bot Manager\n"
            "Доступные команды:\n"
            "/add_bot - добавить нового бота\n"
            "/list_bots - список всех ботов\n"
            "/cancel - отменить текущую операцию"
        )

    @check_access(level="user")
    async def list_bots_handler(self, message: Message):
        if not self.bots:
            await message.answer("ℹ️ Нет добавленных ботов")
            return
            
        response = ["📋 Список ботов:"]
        for name, bot in self.bots.items():
            response.append(
                f"• {name} [{bot.config.type}]\n"
                f"  IP: {bot.config.ip}\n"
                f"  Путь: {bot.config.path}\n"
                f"  Статус: {bot.status}"
            )
        await message.answer("\n".join(response))

    @check_access(level="admin")
    async def cancel_handler(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer("❌ Операция отменена", reply_markup=ReplyKeyboardRemove())

    # --- FSM Handlers ---
    @check_access(level="admin")
    async def add_bot_start(self, message: Message, state: FSMContext):
        await message.answer(
            "Введите уникальное имя для бота:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(AddBotStates.WAITING_NAME)

    async def handle_name(self, message: Message, state: FSMContext):
        if message.text in self.bots:
            await message.answer("⚠️ Бот с таким именем уже существует! Введите другое имя:")
            return
            
        await state.update_data(name=message.text)
        await message.answer("Введите IP-адрес сервера:")
        await state.set_state(AddBotStates.WAITING_IP)

    async def handle_ip(self, message: Message, state: FSMContext):
        if not validate_ip(message.text):
            await message.answer("❌ Неверный формат IP! Попробуйте снова:")
            return
            
        await state.update_data(ip=message.text)
        await message.answer(
            "Введите учетные данные (формат: `login:password` или просто `login` для SSH-ключа):",
            parse_mode="Markdown"
        )
        await state.set_state(AddBotStates.WAITING_CREDENTIALS)

    async def handle_credentials(self, message: Message, state: FSMContext):
        parts = message.text.split(":")
        login = parts[0].strip()
        password = parts[1].strip() if len(parts) > 1 else None
        
        await state.update_data(login=login, password=password)
        data = await state.get_data()
        
        default_path = f"/home/{login}/bots/{data['name']}"
        await message.answer(
            f"Введите путь к боту (по умолчанию: {default_path}):"
        )
        await state.set_state(AddBotStates.WAITING_PATH)

    async def handle_path(self, message: Message, state: FSMContext):
        path = message.text.strip()
        await state.update_data(path=path)
        await message.answer(
            "Введите Git-репозиторий (если есть) или 'пропустить':",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="пропустить")]],
                resize_keyboard=True
            )
        )
        await state.set_state(AddBotStates.WAITING_GIT)

    async def handle_git(self, message: Message, state: FSMContext):
        git_repo = None
        if message.text.lower() != "пропустить":
            if not validate_git(message.text):
                await message.answer("❌ Неверный формат Git URL! Попробуйте снова:")
                return
            git_repo = message.text
            
        await state.update_data(git_repo=git_repo)
        data = await state.get_data()
        
        # Формируем подтверждение
        confirm_text = (
            "🔍 Проверьте данные:\n"
            f"Имя: {data['name']}\n"
            f"IP: {data['ip']}\n"
            f"Логин: {data['login']}\n"
            f"Пароль: {'установлен' if data.get('password') else 'используется SSH-ключ'}\n"
            f"Путь: {data.get('path')}\n"
            f"Git: {data.get('git_repo', 'не указан')}"
        )
        
        await message.answer(
            confirm_text,
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="✅ Подтвердить")],
                    [types.KeyboardButton(text="❌ Отменить")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(AddBotStates.CONFIRMATION)

    async def handle_confirmation(self, message: Message, state: FSMContext):
        if message.text == "❌ Отменить":
            await state.clear()
            await message.answer("❌ Добавление отменено", reply_markup=ReplyKeyboardRemove())
            return
            
        data = await state.get_data()
        bot_name = data["name"]
        
        # Создаем конфиг
        new_config = BotConfig(
            ip=data["ip"],
            login=data["login"],
            password=data.get("password"),
            path=data.get("path"),
            git_repo=data.get("git_repo")
        )
        
        # Проверяем подключение
        try:
            is_connected = await self.ssh.test_connection(new_config)
            if not is_connected:
                raise ConnectionError("SSH connection failed")
        except Exception as e:
            await message.answer(
                f"❌ Ошибка подключения: {str(e)}\n"
                "Проверьте данные и попробуйте снова /add_bot",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            return
            
        # Сохраняем бота
        bots = BotConfigManager.load()
        bots[bot_name] = new_config
        BotConfigManager.save(bots)
        
        self.bots[bot_name] = ManagedBot(config=new_config)
        
        await message.answer(
            f"✅ Бот {bot_name} успешно добавлен!",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
