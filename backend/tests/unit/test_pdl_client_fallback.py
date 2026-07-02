import httpx
import pytest
import respx

from app.config import Settings
from app.services.pdl_client import PDLClient


@pytest.fixture
def client():
    return PDLClient(Settings(_env_file=None, pdl_api_key="test-key"))


@respx.mock
async def test_404_returns_null_field_profile(client):
    respx.get(client._settings.pdl_api_url).mock(return_value=httpx.Response(404))
    profile = await client.enrich_company("Nonexistent Co")
    assert profile.name == "Nonexistent Co"
    assert profile.description is None
    await client.aclose()


@respx.mock
async def test_500_raises_for_caller_to_handle(client):
    respx.get(client._settings.pdl_api_url).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await client.enrich_company("Whatever Co")
    await client.aclose()


@respx.mock
async def test_200_maps_pdl_fields_to_company_profile(client):
    respx.get(client._settings.pdl_api_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "name": "Notion Labs",
                    "description": "Productivity software",
                    "employee_count": 600,
                    "metrics": {"revenue": "$100M-$250M", "funding": "$343M"},
                }
            },
        )
    )
    profile = await client.enrich_company("Notion")
    assert profile.name == "Notion Labs"
    assert profile.employees == 600
    assert profile.estimated_revenue == "$100M-$250M"
    assert profile.total_funding == "$343M"
    await client.aclose()


def test_missing_key_is_not_configured():
    client = PDLClient(Settings(_env_file=None))
    assert client.is_configured() is False
