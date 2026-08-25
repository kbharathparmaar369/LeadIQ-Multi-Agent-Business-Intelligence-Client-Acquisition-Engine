import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from supabase import create_client

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MODEL_SMART = os.getenv("GROQ_MODEL_SMART", "llama-3.3-70b-versatile")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_API")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize Supabase client if credentials are present
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing. Supabase client set to None.")

fast_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0
)

smart_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_SMART,
    temperature=0.5
)


if __name__ == "__main__":
    print("Supabase client:", supabase)
    print("Fast LLM:", fast_llm)
    print("Smart LLM:", smart_llm)


