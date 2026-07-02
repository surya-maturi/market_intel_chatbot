from unittest.mock import AsyncMock

from app.config import Settings
from app.graph.nodes.company_node import make_fetch_company
from app.schemas.company import CompanyProfile
from app.services.crunchbase_client import CrunchbaseClient
from app.services.pdl_client import PDLClient


async def test_missing_pdl_key_propagates_demo_flag_true():
    pdl = PDLClient(Settings(_env_file=None))
    crunchbase = CrunchbaseClient(Settings(_env_file=None))
    node = make_fetch_company(pdl, crunchbase)

    result = await node({"user_query": "Tell me about Notion", "entity": "Notion", "demo_flags": {}})
    assert result["demo_flags"]["company"] is True
    assert result["company_profile"].source == "demo"


async def test_configured_but_failing_pdl_call_propagates_demo_flag_true():
    settings = Settings(_env_file=None, pdl_api_key="test-key")
    pdl = PDLClient(settings)
    pdl.enrich_company = AsyncMock(side_effect=RuntimeError("network error"))
    crunchbase = CrunchbaseClient(settings)
    node = make_fetch_company(pdl, crunchbase)

    result = await node({"user_query": "Tell me about Notion", "entity": "Notion", "demo_flags": {}})
    assert result["demo_flags"]["company"] is True


async def test_successful_live_call_propagates_demo_flag_false():
    settings = Settings(_env_file=None, pdl_api_key="test-key")
    pdl = PDLClient(settings)
    pdl.enrich_company = AsyncMock(return_value=CompanyProfile(name="Notion Labs", source="pdl"))
    crunchbase = CrunchbaseClient(settings)
    node = make_fetch_company(pdl, crunchbase)

    result = await node({"user_query": "Tell me about Notion", "entity": "Notion", "demo_flags": {}})
    assert result["demo_flags"]["company"] is False
    assert result["company_profile"].source == "pdl"
