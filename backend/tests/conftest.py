import pytest

import app.api.deps as deps_module
import app.db.session as db_session_module
from app.config import Settings, get_settings
from app.schemas.company import CompanyProfile
from app.schemas.reddit import RedditPost
from app.services import demo_data

_ENV_KEYS = [
    "PERPLEXITY_API_KEY",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "PDL_API_KEY",
    "CRUNCHBASE_API_KEY",
    "ENABLE_CRUNCHBASE",
]


@pytest.fixture(autouse=True)
def _isolated_test_env(monkeypatch, tmp_path):
    """No test may read real API keys or a real DB, even if the developer later
    adds a live backend/.env file for manual smoke testing."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test_chat_history.db"))
    monkeypatch.setitem(Settings.model_config, "env_file", None)

    get_settings.cache_clear()
    db_session_module._engine = None
    db_session_module._session_factory = None
    deps_module._bundle = None

    yield

    get_settings.cache_clear()
    db_session_module._engine = None
    db_session_module._session_factory = None
    deps_module._bundle = None


@pytest.fixture
def fake_settings() -> Settings:
    """All keys unset -> every service client is forced into demo mode."""
    return Settings(_env_file=None)


@pytest.fixture
def configured_settings() -> Settings:
    return Settings(
        _env_file=None,
        perplexity_api_key="test-perplexity-key",
        reddit_client_id="test-id",
        reddit_client_secret="test-secret",
        pdl_api_key="test-pdl-key",
    )


@pytest.fixture
def sample_posts() -> list[RedditPost]:
    raw = demo_data.load_reddit_demo(["startups"])
    return [RedditPost(**p) for p in raw]


@pytest.fixture
def sample_company_profile() -> CompanyProfile:
    return CompanyProfile(**demo_data.load_pdl_demo("Notion"), source="pdl")
