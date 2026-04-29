import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing required Supabase configuration in .env file. "
        "Please set: SUPABASE_URL and SUPABASE_KEY"
    )

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_conn() -> Client:
    """Get Supabase client instance."""
    return supabase


def test_connection():
    """Test the database connection."""
    try:
        # Test connection by querying a simple table or using health check
        response = supabase.table("information_schema.tables").select("*").limit(1).execute()
        print("✓ Successfully connected to Supabase")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        return False


if __name__ == "__main__":
    test_connection()
