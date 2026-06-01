from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "local"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
