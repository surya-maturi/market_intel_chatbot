# agents/pdl_agent.py

import requests
from requests.exceptions import HTTPError
from utils.config import PDL_API_KEY, PDL_API_URL

def fetch_company_info(company_name: str):
    """
    Use People Data Labs Company Enrichment to fetch
    a company’s description, headcount, revenue, and funding.
    """
    headers = {
        "X-Api-Key": PDL_API_KEY,
        "Content-Type": "application/json"
    }
    params = {"name": company_name}
    try:
        resp = requests.get(PDL_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        result = resp.json().get("data", {})
    except HTTPError as e:
        if resp.status_code == 404:
            # No such company found
            return {
                "name": company_name,
                "description": None,
                "employees": None,
                "estimatedRevenue": None,
                "totalFunding": None
            }
        else:
            raise

    return {
        "name":              result.get("name", company_name),
        "description":       result.get("description"),
        "employees":         result.get("employee_count"),
        "estimatedRevenue":  result.get("metrics", {}).get("revenue"),
        "totalFunding":      result.get("metrics", {}).get("funding")
    }
