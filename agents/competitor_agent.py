import os
import requests
from utils.config import CRUNCHBASE_API_KEY

def fetch_company_info(company_name: str):
    url = f"https://api.crunchbase.com/api/v4/entities/organizations"
    params = {"query": company_name}
    headers = {"X-Crunchbase-User-Key": CRUNCHBASE_API_KEY}
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    items = data.get("entities", [])
    if not items:
        return {"name": company_name, "total_funding_usd": 0, "latest_round": {}, "num_rounds": 0}
    org = items[0]
    profile = org.get("properties", {})
    funding_rounds = profile.get("funding_rounds", [])
    total_funding = sum(fr.get("money_raised_usd", 0) or 0 for fr in funding_rounds)
    latest_round = funding_rounds[-1] if funding_rounds else {}
    return {
        "name": profile.get("name", company_name),
        "total_funding_usd": total_funding,
        "latest_round": latest_round,
        "num_rounds": len(funding_rounds)
    }
