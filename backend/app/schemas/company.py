from pydantic import BaseModel


class CompanyProfile(BaseModel):
    name: str
    description: str | None = None
    employees: int | None = None
    estimated_revenue: str | None = None
    total_funding: str | None = None
    source: str = "pdl"
