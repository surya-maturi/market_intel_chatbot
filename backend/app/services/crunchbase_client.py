from app.config import Settings


class CrunchbaseClient:
    """Optional secondary company-enrichment source. Disabled by default.

    Never makes a network call unless both ENABLE_CRUNCHBASE is true and
    a CRUNCHBASE_API_KEY is configured - is_configured() gates every call site.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def is_configured(self) -> bool:
        return bool(self._settings.enable_crunchbase and self._settings.crunchbase_api_key)

    async def enrich_company(self, company_name: str) -> dict | None:
        if not self.is_configured():
            return None
        # Not implemented in phase 1 (no Crunchbase key available to verify against).
        return None
