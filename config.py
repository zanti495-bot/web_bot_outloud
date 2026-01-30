import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8200746971:AAGkBS64Mn5LJtIlrMMPTZTfCdHdOdUb6Pc")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "393628087"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "aasdJI2j12309LL")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf")
DATABASE_URL = os.getenv("DATABASE_URL")                      # обязательно должен быть в переменных окружения Timeweb
WEBHOOK_DOMAIN = "https://zanti495-bot-web-bot-outloud-3d66.twc1.net"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}"

# Для удобства отладки локально можно раскомментировать:
# from dotenv import load_dotenv
# load_dotenv()
