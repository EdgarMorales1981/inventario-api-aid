import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise RuntimeError(f"Falta SUPABASE_URL en el archivo .env. Buscando en: {ENV_PATH}")

if not SUPABASE_KEY:
    raise RuntimeError(f"Falta SUPABASE_KEY en el archivo .env. Buscando en: {ENV_PATH}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)