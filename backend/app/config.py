from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / '.env'

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_env: str = 'development'
    database_url: str = 'sqlite:///./solarlead.db'
    frontend_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    allowed_hosts: str = 'localhost,127.0.0.1'
    docs_enabled: bool = True

    jwt_secret: str = 'CHANGE-ME-IN-PRODUCTION'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 480
    cookie_secure: bool = False
    cookie_domain: str | None = None

    bootstrap_admin_email: str = 'admin@example.com'
    bootstrap_admin_password: str = 'ChangeMe123!'
    api_key_salt: str = 'CHANGE-ME-API-SALT'
    default_ingestion_api_key: str | None = None

    meta_verify_token: str | None = None
    meta_app_secret: str | None = None

    trust_proxy_headers: bool = False
    public_rate_limit_requests: int = 60
    public_rate_limit_window_seconds: int = 60

    operator_name: str = 'Betreiber dieser Website'
    operator_contact_email: str = ''

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.frontend_origins.split(',') if x.strip()]

    @property
    def hosts(self) -> list[str]:
        return [x.strip() for x in self.allowed_hosts.split(',') if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
