import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class DiscordSender:
    def __init__(self):
        self.free_webhook = os.getenv('DISCORD_FREE_WEBHOOK')
        self.vip_webhook = os.getenv('DISCORD_VIP_WEBHOOK')
        self.admin_webhook = os.getenv('DISCORD_ADMIN_WEBHOOK')
        
        # Используем прокси для Discord
        proxy_url = os.getenv('TELEGRAM_PROXY_URL')
        proxy_user = os.getenv('TELEGRAM_PROXY_USERNAME')
        proxy_pass = os.getenv('TELEGRAM_PROXY_PASSWORD')
        
        self.proxies = None
        if proxy_url and proxy_user and proxy_pass:
            proxy_with_auth = f"http://{proxy_user}:{proxy_pass}@{proxy_url.split('//')[1]}"
            self.proxies = {'http': proxy_with_auth, 'https': proxy_with_auth}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔧 DiscordSender инициализирован")

    def _send(self, webhook, message):
        if not webhook:
            self.logger.warning("❌ Webhook не настроен")
            return False
        try:
            payload = {
                "content": message,
                "username": "Crypto Signals Bot",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/825/825545.png"
            }
            response = requests.post(webhook, json=payload, timeout=30, proxies=self.proxies)
            if response.status_code == 204:
                self.logger.info("✅ Discord сообщение отправлено")
                return True
            else:
                self.logger.error(f"❌ Discord ошибка: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки в Discord: {e}")
            return False

    def send_to_admin(self, message):
        """Отправка в админский канал Discord"""
        return self._send(self.admin_webhook, f"🔧 АДМИН: {message}")

    def send_to_vip(self, message):
        """Отправка в VIP канал Discord"""
        return self._send(self.vip_webhook, f"⭐ VIP: {message}")

    def send_to_free(self, message):
        """Отправка в FREE канал Discord"""
        return self._send(self.free_webhook, f"📢 СИГНАЛ: {message}")

# Глобальный экземпляр
discord_sender = DiscordSender()
