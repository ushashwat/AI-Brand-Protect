"""FastAPI service - exposes the brand intelligence pipeline as a REST endpoint."""

from fastapi import FastAPI, HTTPException
from schemas.schema import BrandProfile, ScanRequest
from main import discover_brand
from utils.helpers import configure_logging, sanitise_domain, validate_company_name

configure_logging("INFO")
app = FastAPI(title="AI-Brand-Protect", version="1.0")


@app.post("/scan", response_model=BrandProfile)
async def scan(req: ScanRequest) -> BrandProfile:
    """Discover and return the brand intelligence profile for a company."""
    try:
        company = validate_company_name(req.company_name)
        domains = [sanitise_domain(d) for d in req.official_domains]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return await discover_brand(company, domains)
