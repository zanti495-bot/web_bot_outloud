import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')  # Не используется, т.к. покупки условные

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/bot_outloud')

# Webhook
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://yourdomain.com')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Mini App URL
MINI_APP_URL = f"{WEBHOOK_HOST}/webapp/"

# Flask Admin
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'secret')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpass')

# Admin ID for Telegram admin commands
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 123456789))  # Ваш Telegram ID

# Design settings (default)
DEFAULT_DESIGN = {
    'background_color': '#FFFFFF',
    'text_color': '#000000',
    'font_family': 'Arial',
}