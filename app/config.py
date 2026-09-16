"""应用配置：从 .env 加载 LLM、数据库、JWT 与运行时限制。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """环境变量映射；未设置项使用下方默认值。"""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    qwen_api_key: str = ""
    qwen_base_url: str = ""
    qwen_model: str = "Qwen2-72B-Instruct"

    tavily_api_key: str = ""

    use_mock_db: bool = True
    mysql_dsn: str = "mysql://root:password@127.0.0.1:3306/enterprise_ops"

    jwt_secret: str = "change-me-in-production-use-at-least-32-chars"
    jwt_expire_minutes: int = 720
    jwt_algorithm: str = "HS256"

    max_tool_rounds: int = 8
    task_timeout_s: float = 30
    reports_dir: str = "reports"

    kb_enabled: bool = False
    kb_base_url: str = ""
    kb_api_key: str = ""
    kb_timeout_s: float = 3

    log_retention_days: int = 60

    demo_ops_username: str = "ops"
    demo_ops_password: str = "ops123"
    demo_dev_username: str = "dev"
    demo_dev_password: str = "dev123"


@lru_cache
def get_settings() -> Settings:
    """单例 Settings，进程内缓存。"""
    return Settings()


def reports_path() -> Path:
    """解析并确保 reports 目录存在（相对 ROOT_DIR）。"""
    path = Path(get_settings().reports_dir)
    if not path.is_absolute():
        path = ROOT_DIR / path
    path.mkdir(parents=True, exist_ok=True)
    return path
