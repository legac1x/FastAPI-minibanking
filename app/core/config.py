from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv()
    )

    SECRET_KEY: str
    ALGORITHM: str
    EMAIL_HOST: str
    EMAIL_PASSWORD: str

    @property
    def ASYNC_DATABASE_URL(self):
        return "sqlite+aiosqlite:///mydb.db"

settings = Settings()