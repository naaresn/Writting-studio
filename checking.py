import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)
client = genai.Client()

for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(m.name)