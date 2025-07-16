# agents/synthesizer_agent.py

import requests
from utils.config import PERPLEXITY_API_KEY

API_URL = "https://api.perplexity.ai/chat/completions"

def synthesize_insight(user_query: str, posts, sentiments):
    examples = "\n".join(f"- {p['title']}" for p in posts[:5])
    avg_sent  = sum(sentiments)/len(sentiments) if sentiments else 0
    sent_desc = "positive" if avg_sent > 0.05 else "negative" if avg_sent < -0.05 else "neutral"
    prompt = (
        f"User query: {user_query}\n"
        f"Example posts:\n{examples}\n"
        f"Overall sentiment: {sent_desc} (avg={avg_sent:.2f}).\n"
        "Summarize what's happening and suggest actions for a startup founder."
    )
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a market intelligence assistant."},
            {"role": "user",   "content": prompt}
        ]
    }
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
