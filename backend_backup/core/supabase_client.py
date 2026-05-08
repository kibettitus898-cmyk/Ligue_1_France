import threading
from supabase import create_client, Client
from backend.core.config import settings

_thread_local = threading.local()

def get_supabase() -> Client:
    """Return a thread-local Supabase client (safe for FastAPI threadpool)."""
    client = getattr(_thread_local, "client", None)
    if client is None:
        _thread_local.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    return _thread_local.client