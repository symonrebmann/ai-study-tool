
from google import genai
from dotenv import load_dotenv
import os

load_dotenv(".env.txt")

api_key: str | None = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not set. Check your .env file.")
    exit()

client = genai.Client(api_key=api_key)

