from pydantic_settings import BaseSettings
from pydantic import Field
import os


def generate_secret_key():
    return os.urandom(24).hex()


class Settings(BaseSettings):
    MONGODB_URI: str
    REDIS_URI: str
    SECRET_KEY: str = Field(default_factory=generate_secret_key)
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
