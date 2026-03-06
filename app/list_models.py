from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("\nAVAILABLE MODELS:\n")
for m in client.models.list():
    print(m.name)
