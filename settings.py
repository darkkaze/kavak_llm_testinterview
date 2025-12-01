import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Twilio WhatsApp
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "kavak.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Model Configuration
MODEL_NAME = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"

# Language (es/en)
LANGUAGE = os.getenv("LANGUAGE", "es")
