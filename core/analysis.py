"""
Extracts keywords, key executives, and social media footprints
using Tavily web search and OpenAI structured outputs.
"""

import asyncio
import httpx
from pydantic import BaseModel
from typing import Any
import config
from schemas.schema import KeywordResponse, Person, PeopleResponse, SocialResponse


async def _tavily_search(query: str, web: httpx.AsyncClient) -> list[dict]:
    """Execute dynamic web searches via the Tavily API."""
    if not config.tavily_api_key:
        return []

    payload = {
        "api_key": config.tavily_api_key,
        "query": query,
        "max_results": 5,
        "search_depth": "advanced",
    }
    try:
        resp = await web.post(
            "https://api.tavily.com/search",
            json=payload,
            timeout=config.request_timeout,
        )
        return resp.json().get("results", [])
    except Exception:
        return []


async def _openai_structured(prompt: str, schema: type[BaseModel]) -> Any:
    """Parse unstructured text into validated Pydantic models using OpenAI."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
    )
    resp = await client.beta.chat.completions.parse(
        model=config.openai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format=schema,
    )
    return resp.choices[0].message.parsed


async def extract_keywords(company: str, web: httpx.AsyncClient) -> list[str]:
    """Infer relevant business keywords and tags based on web search context."""
    results = await _tavily_search(f"{company} company profile industry products", web)
    search_text = "\n\n".join([r.get("content", "") for r in results])

    prompt = (
        f"Map '{company}' to EXACTLY 5-10 strict 'Global Industry Classification Standard' (GICS) structural descriptors.\n"
        f"Avoid adjectives. Use standard taxonomic nouns (e.g. 'Software infrastructure', 'Consumer electronics').\n\n"
        f"Context:\n{search_text}"
    )
    try:
        ai_resp = await _openai_structured(prompt, KeywordResponse)
        return sorted({k.strip().lower() for k in ai_resp.keywords if len(k) < 40})
    except Exception:
        return []


async def extract_people(company: str, web: httpx.AsyncClient) -> list[Person]:
    """Extract key personnel using Tavily search and OpenAI structuring."""
    results = await _tavily_search(
        f"{company} key executives CEO founders leadership board official site",
        web,
    )
    search_text = "\n\n".join([r.get("content", "") for r in results])

    fallback_url = (
        f"https://www.google.com/search?q={company.replace(' ', '+')}+executives"
    )

    prompt = (
        f"Extract key executives, founders, and leadership for '{company}'.\n"
        f"For each person, you MUST provide a 'source_url' (required field).\n"
        f"If the exact URL is missing in the context, use '{fallback_url}' as a fallback.\n"
        f"Context:\n{search_text}"
    )
    try:
        ai_resp = await _openai_structured(prompt, PeopleResponse)
        return [p for p in ai_resp.people if p.name]
    except Exception:
        return []


async def extract_socials(company: str, web: httpx.AsyncClient) -> list[str]:
    """Extract official social media profiles for the company."""
    results = await _tavily_search(
        f"{company} official social media profiles linkedin instagram tiktok youtube twitter x",
        web,
    )
    search_text = "\n\n".join([r.get("content", "") for r in results])

    prompt = (
        f"Extract all official social media profile URLs for '{company}'.\n"
        f"Return only the exact validated profile URLs.\n"
        f"Context:\n{search_text}"
    )
    try:
        ai_resp = await _openai_structured(prompt, SocialResponse)
        candidates = ai_resp.social_urls

        async def _verify(url: str) -> str | None:
            """Return the URL only if it resolves to a real page."""
            try:
                resp = await web.head(url, follow_redirects=True, timeout=8.0)
                return url if resp.status_code < 400 else None
            except Exception:
                return None

        results_verified = await asyncio.gather(*[_verify(u) for u in candidates])
        return [u for u in results_verified if u is not None]
    except Exception:
        return []
