# utils/config.py

from dotenv import load_dotenv
load_dotenv()      # ← makes os.getenv(...) see your .env

import os

# LLM API Keys
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")

# Reddit
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT    = "market-intel-chatbot"

# People Data Labs
PDL_API_KEY = os.getenv("PDL_API_KEY")
PDL_API_URL = "https://api.peopledatalabs.com/v5/company/enrich"

# Database
DB_PATH = os.getenv("DB_PATH", "chat_history.db")
