from app.schemas.company import CompanyProfile
from app.services.base_client import BaseAPIClient


class PDLClient(BaseAPIClient):
    def is_configured(self) -> bool:
        return bool(self._settings.pdl_api_key)

    async def enrich_company(self, company_name: str) -> CompanyProfile:
        headers = {"X-Api-Key": self._settings.pdl_api_key, "Content-Type": "application/json"}
        params = {"name": company_name}
        resp = await self.request_with_retry(
            "GET", self._settings.pdl_api_url, headers=headers, params=params
        )
        if resp.status_code == 404:
            return CompanyProfile(name=company_name)
        resp.raise_for_status()
        data = resp.json().get("data", {}) or {}
        metrics = data.get("metrics", {}) or {}
        return CompanyProfile(
            name=data.get("name", company_name),
            description=data.get("description"),
            employees=data.get("employee_count"),
            estimated_revenue=metrics.get("revenue"),
            total_funding=metrics.get("funding"),
            source="pdl",
        )
