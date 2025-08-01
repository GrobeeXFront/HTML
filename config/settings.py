import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    def __init__(self):
        # ???????? ???????????? ??????????
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN ?? ????? ? .env")
        
        # ??????? ?????? ???????????????
        admins = os.getenv("ADMINS", "")
        self.ADMINS = [int(admin_id.strip()) for admin_id in admins.split(",") if admin_id.strip()]
        
        # SSH ?????????
        self.SSH_USER = os.getenv("SSH_USER", "ubuntu")
        self.SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")
        
        # ?????????????? ????????
        if not self.ADMINS:
            print("?? ????????: ?? ?????? ?? ?????? ?????????????? ? ADMINS")
        
        if not self.SSH_KEY_PATH or not os.path.exists(self.SSH_KEY_PATH):
            print("?? ????????: SSH ???? ?? ?????? ??? ???? ????????")

settings = Settings()