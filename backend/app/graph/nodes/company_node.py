from app.graph.state import ChatState
from app.schemas.company import CompanyProfile
from app.services import demo_data
from app.services.crunchbase_client import CrunchbaseClient
from app.services.fallback import call_with_fallback
from app.services.pdl_client import PDLClient


def make_fetch_company(pdl_client: PDLClient, crunchbase_client: CrunchbaseClient):
    async def fetch_company(state: ChatState) -> dict:
        company_name = (state.get("entity") or state["user_query"]).strip()

        async def live_call() -> CompanyProfile:
            return await pdl_client.enrich_company(company_name)

        def demo_call() -> CompanyProfile:
            return CompanyProfile(**demo_data.load_pdl_demo(company_name), source="demo")

        profile, used_demo = await call_with_fallback(
            "company", pdl_client.is_configured(), live_call, demo_call
        )

        if crunchbase_client.is_configured():
            cb_data = await crunchbase_client.enrich_company(company_name)
            if cb_data:
                profile = profile.model_copy(update={"source": f"{profile.source}+crunchbase"})

        demo_flags = dict(state.get("demo_flags", {}))
        demo_flags["company"] = used_demo

        return {"company_profile": profile, "demo_flags": demo_flags}

    return fetch_company
