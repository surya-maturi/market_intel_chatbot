from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    perplexity_api_key: str | None = None
    perplexity_model: str = "sonar"

    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "market-intel-chatbot/2.0"

    pdl_api_key: str | None = None
    pdl_api_url: str = "https://api.peopledatalabs.com/v5/company/enrich"

    enable_crunchbase: bool = False
    crunchbase_api_key: str | None = None

    db_path: str = "data/chat_history.db"

    cors_origins: list[str] = ["http://localhost:3000"]

    request_timeout_seconds: float = 15.0
    max_retries: int = 2

    log_level: str = "INFO"
    log_json: bool = False

    @property
    def service_status(self) -> dict[str, str]:
        return {
            "perplexity": "configured" if self.perplexity_api_key else "demo",
            "reddit": "configured" if (self.reddit_client_id and self.reddit_client_secret) else "demo",
            "pdl": "configured" if self.pdl_api_key else "demo",
            "crunchbase": (
                "configured"
                if (self.enable_crunchbase and self.crunchbase_api_key)
                else "disabled"
            ),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
