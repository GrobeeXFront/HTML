import asyncssh
from config import settings
from config.bots_config import BotConfig  # Добавляем импорт BotConfig

class SSHManager:
    async def execute_command(self, host: str, port: int, command: str) -> str:
        """Выполнение команды на удаленном сервере"""
        try:
            async with asyncssh.connect(
                host=host,
                port=port,
                username=settings.SSH_USER,
                client_keys=[settings.SSH_KEY_PATH]
            ) as conn:
                result = await conn.run(command)
                return result.stdout if result.exit_status == 0 else f"ERROR: {result.stderr}"
        except Exception as e:
            return f"SSH Connection failed: {str(e)}"

    async def get_bot_logs(self, host: str, port: int, bot_name: str, lines: int = 50) -> str:
        """Получение логов через journalctl"""
        cmd = f"journalctl -u {bot_name} -n {lines} --no-pager"
        return await self.execute_command(host, port, cmd)

    async def test_connection(self, config: BotConfig) -> bool:
        """Проверка соединения с сервером"""
        try:
            async with asyncssh.connect(
                host=config.ip,
                port=config.port,
                username=config.login,
                password=config.password,
                client_keys=[settings.SSH_KEY_PATH] if not config.password else None
            ) as conn:
                return True
        except Exception:
            return False