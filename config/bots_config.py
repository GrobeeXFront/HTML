from dataclasses import dataclass
from typing import Dict, Any, Optional  # Добавляем Optional
import json
from pathlib import Path

@dataclass
class BotConfig:
    """Конфигурация одного бота"""
    ip: str
    login: str
    password: Optional[str] = None
    path: Optional[str] = None
    git_repo: Optional[str] = None
    type: str = "default"  # Например: "telegram", "discord" и т.д.

class BotConfigManager:
    """Менеджер для работы с конфигурацией ботов"""
    
    CONFIG_FILE = "bots.json"  # Файл для хранения конфигов
    
    @staticmethod
    def load() -> Dict[str, BotConfig]:
        """Загружает конфигурацию ботов из файла"""
        try:
            with open(BotConfigManager.CONFIG_FILE) as f:
                data = json.load(f)
            return {name: BotConfig(**config) for name, config in data.items()}
        except FileNotFoundError:
            return {}  # Если файла нет - возвращаем пустой словарь
    
    @staticmethod
    def save(bots: Dict[str, BotConfig]):
        """Сохраняет конфигурацию ботов в файл"""
        data = {name: vars(config) for name, config in bots.items()}
        with open(BotConfigManager.CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)