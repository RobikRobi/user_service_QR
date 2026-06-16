from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent


class AuthData(BaseModel):

    private_key: Path = BASE_DIR /"tokens"/"jwt-private.pem"
    public_key: Path = BASE_DIR /"tokens"/"jwt-public.pem"
    algorithm: str = 'RS256'
    days: int = 15


class EnvData(BaseSettings):

    USERS_DATABASE_URL: str
    model_config = SettingsConfigDict(env_file='.env')


class Config(BaseModel):

    env_data:EnvData = EnvData()
    auth_data:AuthData = AuthData()

    
config = Config()