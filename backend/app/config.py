from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    anthropic_api_key: str = ""
    psx_api_url: str = ""
    telegram_bot_token: str = ""
    secret_key: str = "dev-secret"

    class Config:
        env_file = ".env"


settings = Settings()
