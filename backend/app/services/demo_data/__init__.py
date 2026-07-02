import json
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).parent


@lru_cache
def _load(filename: str) -> dict:
    with open(_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def load_reddit_demo(topic_keywords: list[str]) -> list[dict]:
    data = _load("reddit_demo.json")
    key = next((k for k in data if k != "default" and k.lower() in " ".join(topic_keywords).lower()), None)
    return data.get(key or "default", data["default"])


def load_pdl_demo(company_name: str) -> dict:
    data = _load("pdl_demo.json")
    key = next((k for k in data if k != "default" and k.lower() == company_name.lower()), None)
    profile = dict(data.get(key or "default", data["default"]))
    if not key:
        profile["name"] = company_name
    return profile


def load_intent_demo() -> dict:
    return _load("perplexity_intent_demo.json")


def load_synthesis_demo() -> dict:
    return _load("perplexity_synthesis_demo.json")
