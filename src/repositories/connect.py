import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "không có biến môi trường SUPABASE_URL hoặc SUPABASE_KEY. "
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def conn() -> Client:
    return supabase


def test_connection():
    """Test the database connection."""
    try:
        # Test connection by querying a simple table or using health check
        response = supabase.table("test").select("*").limit(1).execute()
        print("✓ Successfully connected to Supabase")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        return False


if __name__ == "__main__":
    test_connection()
