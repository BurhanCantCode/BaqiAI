from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    anthropic_api_key: str = ""
    psx_api_url: str = ""
    telegram_bot_token: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""
    secret_key: str = "dev-secret"
    groq_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
