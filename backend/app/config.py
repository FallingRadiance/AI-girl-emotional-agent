import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Shanghai")


settings = Settings()
