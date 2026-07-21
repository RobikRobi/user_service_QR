from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent


class AuthData(BaseModel):

    private_key: Path = BASE_DIR /"app"/"tokens"/"jwt-private.pem"
    public_key: Path = BASE_DIR /"app"/"tokens"/"jwt-public.pem"
    algorithm: str = 'RS256'
    munites: int = 30
    days: int = 15


class EnvData(BaseSettings):

    USERS_DATABASE_URL: str
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    JWT_PRIVATE_KEY_PATH: Path | None = None
    JWT_PUBLIC_KEY_PATH: Path | None = None
    JWT_ALGORITHM: str | None = None
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', extra='ignore')

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


class Config(BaseModel):

    env_data:EnvData = EnvData()
    auth_data:AuthData = AuthData()

    def model_post_init(self, __context):
        if self.env_data.JWT_PRIVATE_KEY_PATH:
            self.auth_data.private_key = self._resolve_path(self.env_data.JWT_PRIVATE_KEY_PATH)
        if self.env_data.JWT_PUBLIC_KEY_PATH:
            self.auth_data.public_key = self._resolve_path(self.env_data.JWT_PUBLIC_KEY_PATH)
        if self.env_data.JWT_ALGORITHM:
            self.auth_data.algorithm = self.env_data.JWT_ALGORITHM

    def _resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        resolved = BASE_DIR / path
        if resolved.exists():
            return resolved
        return BASE_DIR / "app" / path

    
config = Config()
