# Project Analysis

## 1. Time Spent
- **Read-up & planning:** ~1 hour for reading up on key cybersecurity terms, requirements, architecture design, & setup.
- **Implementation:** ~2-3 hrs for schemas, brand profile extractors, pipeline, guardrails, & FastAPI server.
- **Testing & documentation:** ~30 min for pytest, containerisation, & documentation.

## 2. Automated Components
Using a company name and one (or more) seed domains, the system automatically discovers:

| Signal | Method |
|---|---|
| Additional owned domains | Tavily search -> LLM inference -> RDAP ownership validation |
| Brand visual assets | HTML scraping |
| Industry keywords | Tavily search -> LLM mapped to GICS taxonomy |
| Key executives | Tavily search -> LLM structured extraction |
| Social media profiles | Tavily search -> LLM URL extraction |

## 3. Assumptions
- **Tavily as the search layer:** Tavily's advanced search index provides structured snippets that are reliable for LLM context. I have previously used Tavily API for my own custom platform (RoboTimes) so I had already tested its capabilities. I did not want to rely on classical web scraping too much as it is often not reliable.
- **RDAP coverage is partial:** Many ccTLD registrars do not participate in the IANA RDAP bootstrap. Domains where RDAP returns no record are correctly left as `is_confirmed_owned: false` (to avoid guessing).

## 4. Trade-offs
- **LLM for inference only:** The LLM is only used to infer domain names and extract structured data from search snippets. Ownership is always confirmed deterministically.
- **Single-pass pipeline over agentic loop:** All five extractors run concurrently and aggregate once. No advanced agentic orchestration was used due to time constraints.
- **Google Search fallback for people:** When Tavily search snippets don't contain a source URL for an executive, the prompt instructs the LLM to use a Google Search URL as the `source_url` fallback. This keeps the `Person` schema valid without hallucinating fake URLs.
- **External rate limits:** Beyond Tavily and OpenAI, RDAP registry servers have undocumented limits that can trigger throttling, resulting in `is_confirmed_owned: false`. Also, few social media platforms block programmatic HEAD requests, thus dropping their social links from output.