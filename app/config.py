"""
应用配置：从环境变量读取。
使用 pydantic-settings，支持 .env。
本工具使用独立 SQLite 库 phone_competitor.db。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 服务
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    # CORS 允许的前端来源，逗号分隔，例如 "https://your-domain.com,https://www.your-domain.com"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # 数据库：本工具专用
    database_url: str = "sqlite:///./data/phone_competitor.db"

    # DeepSeek API
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: int = 120

    # 抓取（间隔过短易触发 GSMArena 429 限流，建议 20～30 秒）
    gsmarena_request_delay_seconds: float = 20.0
    gsmarena_timeout_seconds: int = 30

    # 默认市场与币种（可被前端设置覆盖）
    default_currency: str = "CNY"
    default_market_region: str = "CN"


settings = Settings()
