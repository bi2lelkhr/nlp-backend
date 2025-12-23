# from supabase import create_client
# import os
# from dotenv import load_dotenv

# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

from postgrest import SyncPostgrestClient
import os
from dotenv import load_dotenv
import httpx
from httpx import Timeout

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Create a custom HTTP client with longer timeouts
timeout = Timeout(timeout=30.0, connect=10.0)
http_client = httpx.Client(timeout=timeout)

# Use SyncPostgrestClient for synchronous operations
supabase = SyncPostgrestClient(
    base_url=f"{SUPABASE_URL}/rest/v1",
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    },
    http_client=http_client
)