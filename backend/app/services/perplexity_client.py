import json
import re
from typing import Any

from app.services.base_client import BaseAPIClient

API_URL = "https://api.perplexity.ai/chat/completions"

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class PerplexityClient(BaseAPIClient):
    def is_configured(self) -> bool:
        return bool(self._settings.perplexity_api_key)

    async def chat(self, system: str, user: str) -> str:
        payload = {
            "model": self._settings.perplexity_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        resp = await self._post(payload)
        return resp["choices"][0]["message"]["content"]

    async def chat_json(self, system: str, user: str, schema: dict[str, Any], schema_name: str) -> dict:
        payload = {
            "model": self._settings.perplexity_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema},
            },
        }
        resp = await self._post(payload)
        content = resp["choices"][0]["message"]["content"]
        return _parse_json_content(content)

    async def _post(self, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self._settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        resp = await self.request_with_retry("POST", API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _parse_json_content(content: str) -> dict:
    cleaned = _THINK_BLOCK_RE.sub("", content).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = _JSON_OBJECT_RE.search(cleaned)
        if not match:
            raise
        return json.loads(match.group(0))
