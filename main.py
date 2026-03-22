"""AI-Brand-Protect main entry point."""

import asyncio
import json
import sys
from pathlib import Path
from pydantic import ValidationError
import httpx
import config
from utils.helpers import (
    configure_logging,
    get_logger,
    sanitise_domain,
    validate_company_name,
)
from core.analysis import extract_keywords, extract_people, extract_socials
from core.discovery import extract_assets, extract_domains
from schemas.schema import BrandProfile

configure_logging("INFO")
logger = get_logger(__name__)

INPUT_FILE = Path("brand_input.json")
OUTPUT_DIR = Path("output")


async def discover_brand(company_name: str, domains: list[str]) -> BrandProfile:
    """Run all extraction strategies concurrently and aggregate results."""
    async with httpx.AsyncClient(
        timeout=config.request_timeout, follow_redirects=True
    ) as web:
        tasks = [
            extract_domains(company_name, domains, web),
            extract_assets(domains, web),
            extract_keywords(company_name, web),
            extract_people(company_name, web),
            extract_socials(company_name, web),
        ]
        disc_domains, assets, keywords, people, socials = await asyncio.gather(*tasks)

    return BrandProfile(
        company_name=company_name,
        official_domains=domains,
        discovered_domains=disc_domains,
        visual_assets=assets,
        keywords=keywords,
        key_people=people,
        social_links=socials,
    )


async def main() -> None:
    if not INPUT_FILE.is_file():
        logger.error(f"Input file not found {INPUT_FILE}")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        company = validate_company_name(data.get("company_name", ""))
        domains = [sanitise_domain(str(d)) for d in data.get("official_domains", [])]

        logger.info(f"Discovering brand intelligence for '{company}'...")
        profile = await discover_brand(company, domains)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = (
            OUTPUT_DIR / f"{company.lower().replace(' ', '_')}_brand_profile.json"
        )

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(profile.model_dump_json(indent=2))

        logger.info(f"Success! Profile saved to: {out_path}")
    except ValidationError as exc:
        logger.error(f"Data validation error:\n{exc}")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
