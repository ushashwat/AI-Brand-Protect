"""
Responsible for finding related brand domains, performing RDAP lookups,
and scraping visual assets like logos and favicons.
"""

import asyncio
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
import config
from core.analysis import _openai_structured, _tavily_search
from schemas.schema import Asset, AssetType, DomainInfo, DomainResponse
from utils.helpers import is_safe_url, sanitise_domain


async def _fetch_rdap_bootstrap(web: httpx.AsyncClient) -> dict:
    """Fetch the IANA RDAP bootstrap registry once for reuse across all lookups."""
    try:
        r = await web.get(
            "https://data.iana.org/rdap/dns.json", timeout=config.request_timeout
        )
        return r.json()
    except Exception:
        return {}


async def _rdap_lookup(
    domain: str, web: httpx.AsyncClient, bootstrap: dict
) -> DomainInfo:
    """Query the appropriate RDAP server to confirm domain registration and ownership."""
    try:
        parts = domain.split(".")
        registrable = ".".join(parts[-2:]) if len(parts) > 2 else domain

        tld = registrable.rsplit(".", 1)[-1]
        base_url = next(
            (
                s[0].rstrip("/") + "/"
                for (t, s) in bootstrap.get("services", [])
                if tld in t and s
            ),
            None,
        )
        if base_url and is_safe_url(url := f"{base_url}domain/{registrable}"):
            resp = await web.get(url, timeout=config.request_timeout)
            if resp.status_code == 200:
                data = resp.json()
                org = next(
                    (
                        str(f[3])
                        for e in data.get("entities", [])
                        if "registrant" in e.get("roles", [])
                        for f in e.get("vcardArray", [0, []])[1]
                        if f[0] == "org"
                    ),
                    None,
                )
                return DomainInfo(
                    domain=domain, registrant_org=org, is_confirmed_owned=True
                )
    except Exception:
        pass
    return DomainInfo(domain=domain)


async def extract_domains(
    company: str, seeds: list[str], web: httpx.AsyncClient
) -> list[DomainInfo]:
    """Extract associated global domains intelligently using Search and LLM inference."""
    results = await _tavily_search(
        f"{company} official corporate websites subsidiary domains", web
    )
    search_text = "\n\n".join(
        [r.get("content", "") + " " + r.get("url", "") for r in results]
    )

    prompt = (
        f"You are an expert OSINT investigator finding domains strictly owned by '{company}'.\n"
        f"The company already owns the root domains: {seeds}.\n"
        f"Extract their official subdomains AND any other official corporate domains they explicitly own.\n"
        f"CRITICAL RULES:\n"
        f"1. You MUST explicitly exclude partner companies, customers, and competitors.\n"
        f"2. Only output domains where '{company}' is the owner and operator.\n\n"
        f"Context:\n{search_text}"
    )

    bootstrap = await _fetch_rdap_bootstrap(web)
    found: dict[str, DomainInfo] = {}

    for d in await asyncio.gather(*[_rdap_lookup(s, web, bootstrap) for s in seeds]):
        found[d.domain] = d

    try:
        ai_resp = await _openai_structured(prompt, DomainResponse)
        discovered = set()

        for dom_str in ai_resp.domains:
            try:
                dom = sanitise_domain(dom_str)
                if len(dom.split(".")) >= 2 and dom not in seeds:
                    discovered.add(dom)
            except ValueError:
                pass

        # 1. Subdomains of a seed: ownership is certain, no RDAP needed
        # 2. New root domains: ownership must be confirmed via RDAP
        seed_roots = {s.split(".")[-2] + "." + s.split(".")[-1] for s in seeds}

        subdomain_of_seed: set[str] = set()
        new_roots: set[str] = set()
        for dom in discovered:
            parts = dom.split(".")
            root = parts[-2] + "." + parts[-1]
            if root in seed_roots:
                subdomain_of_seed.add(dom)
            else:
                new_roots.add(dom)

        for dom in subdomain_of_seed:
            found.setdefault(dom, DomainInfo(domain=dom, is_confirmed_owned=True))

        hydrated = await asyncio.gather(
            *[_rdap_lookup(d, web, bootstrap) for d in new_roots],
            return_exceptions=True,
        )
        for result in hydrated:
            if isinstance(result, DomainInfo):
                found.setdefault(result.domain, result)

    except Exception:
        pass

    for s in seeds:
        found.pop(s, None)

    return list(found.values())


async def extract_assets(seeds: list[str], web: httpx.AsyncClient) -> list[Asset]:
    """Gather brand logos and favicons by securely fetching root domain HTML metadata."""
    assets: list[Asset] = []
    seen: set[str] = set()

    for domain in seeds:
        url = f"https://{domain}"
        try:
            html = (
                await web.get(
                    url, follow_redirects=True, timeout=config.request_timeout
                )
            ).text
            soup = BeautifulSoup(html, "html.parser")

            og = soup.find("meta", property="og:image")
            if og and (im_url := str(og.get("content", ""))) and is_safe_url(im_url):
                assets.append(
                    Asset(
                        url=im_url,
                        asset_type=AssetType.logo,
                        source_page=url,
                        description="OpenGraph image",
                    )
                )
                seen.add(im_url)

            for rel in [["icon"], ["shortcut", "icon"], ["apple-touch-icon"]]:
                if (link := soup.find("link", rel=rel)) and (href := link.get("href")):
                    full_url = urljoin(url, str(href))
                    rel_label = "-".join(rel)
                    if is_safe_url(full_url) and full_url not in seen:
                        assets.append(
                            Asset(
                                url=full_url,
                                asset_type=AssetType.favicon,
                                source_page=url,
                                description=f"Favicon ({rel_label})",
                            )
                        )
                        seen.add(full_url)
        except Exception:
            pass

        fav_ico = f"{url}/favicon.ico"
        if fav_ico not in seen:
            try:
                if (
                    await web.head(fav_ico, follow_redirects=True, timeout=5.0)
                ).status_code == 200:
                    assets.append(
                        Asset(
                            url=fav_ico,
                            asset_type=AssetType.favicon,
                            source_page=url,
                            description="Favicon (favicon.ico)",
                        )
                    )
                    seen.add(fav_ico)
            except Exception:
                pass

    return assets
