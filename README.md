# AI-Brand-Protect

An AI-powered brand onboarding agent for brand protection platforms.

Given only a **company name** and **one or more official domains**, it automatically discovers and compiles a comprehensive `BrandProfile`.

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.13, asyncio |
| Schemas | Pydantic |
| LLM | OpenAI |
| Search | Tavily API |
| Domain verification | IANA RDAP bootstrap |
| API server | FastAPI + Uvicorn |
| Containerisation | Docker |

## Pipeline Flow

```
brand_input.json  (or POST /scan body)
│
main.py / server.py
│  (validate inputs)
│
asyncio.gather - five extractors run concurrently:
├── extract_domains -> Tavily search -> LLM -> RDAP validation
├── extract_assets -> HTTP scrape (og:image, favicons)
├── extract_keywords -> Tavily search -> LLM (GICS taxonomy)
├── extract_people -> Tavily search -> LLM structured extraction
└── extract_socials -> Tavily search -> LLM URL extraction
│
BrandProfile (Pydantic)
│
├── API mode  -> JSON response body
└── CLI mode  -> output/<company>_brand_profile.json
```

## Output Schema

| Field | Description |
|---|---|
| `discovered_domains` | Related domains with RDAP ownership confirmation |
| `visual_assets` | Logo and favicon URLs with source and type |
| `keywords` | GICS-mapped industry taxonomy terms |
| `key_people` | Executives with name, role, and source URL |
| `social_links` | Official social media profile URLs |

## Potential Next Steps

1. **Vision Model:** Pass discovered logo URLs to a vision model to confirm logo for [Company].
2. **DNS Validation:** Resolve discovered domains against public DNS to filter parked or stale domains.
3. **Agentic Loop:** Replace single-pass extraction with an agentic loop for refined & validated results.
4. **Log Redaction:** Custom logging formatter that scrubs API key patterns before output.
5. **LLM Fallback:** Support a secondary model if the primary is unavailable.
6. **Contact Emails:** Extend social extraction to also get official customer support emails.

> See [`how_to_run.md`](how_to_run.md) to get started. See [`analysis.md`](analysis.md) for implementation decisions.