from supabase import create_client, Client

from app.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_supabase() -> Client:
    """FastAPI dependency that returns the Supabase client."""
    return supabase
