from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils.logger import get_logger

logger = get_logger("config")


class Settings(BaseSettings):
    API_URL: str
    API_KEY: str
    MEDIA_ROOT: str = "./media"
    PUBLIC_BASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8"
    )


logger.info("开始加载应用配置...")
try:
    settings = Settings()
    logger.info("配置加载成功")
    logger.info(f"API_URL: {settings.API_URL}")
    logger.info(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    logger.info(f"PUBLIC_BASE_URL: {settings.PUBLIC_BASE_URL}")
except Exception as e:
    logger.error(f"配置加载失败: {e}")
    raise