import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY was not found in .env")

print("Connecting to Gemini...")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=20.0,
    max_retries=0,
)

try:
    response = client.chat.completions.create(
        model="gemini-3.6-flash",
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence.",
            }
        ],
        temperature=0.2,
        max_tokens=50,
    )

    print("Gemini response:")
    print(response.choices[0].message.content)

except Exception as error:
    print("Gemini request failed:")
    print(type(error).__name__)
    print(error)

