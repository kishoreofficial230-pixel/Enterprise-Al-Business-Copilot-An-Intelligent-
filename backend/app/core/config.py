from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "root"
    DATABASE_HOST: str = "127.0.0.1"
    DATABASE_PORT: int = 3306
    DATABASE_NAME: str = "enterprise_ai"

    SECRET_KEY: str = "enterprise-ai-business-copilot-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()