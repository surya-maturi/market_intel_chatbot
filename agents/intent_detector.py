# agents/intent_detector.py

import re
import requests
from utils.config import PERPLEXITY_API_KEY

API_URL = "https://api.perplexity.ai/chat/completions"

def detect_intent(query: str):
    # Call Perplexity to classify intent
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Identify intent as 'trend', 'competitor', or 'sentiment'."},
            {"role": "user",   "content": query}
        ]
    }
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].lower()

    # Determine intent and extract entities
    if "competitor" in content:
        # Try to pull out just the company name (e.g. after "about" or "for")
        m = re.search(r'(?:about|for)\s+([A-Za-z0-9 &\\-\\.]+)', query, re.IGNORECASE)
        company = m.group(1).strip() if m else query.strip()
        return "competitor", company

    if "trend" in content:
        return "trend", query

    return "sentiment", query
