# How to Run

## Prerequisites
Copy the environment template and fill in your API keys:
```bash
cp .env.example .env
```
- `OPENAI_API_KEY` - for LLM structured extraction
- `TAVILY_API_KEY` - for web search context

Get a free Tavily API key from [Tavily](https://www.tavily.com/).

## Option A: Docker (Recommended)

```bash
docker compose up --build
```

The server starts at `http://localhost:8000`.
Open **`http://localhost:8000/docs`** for interactive Swagger UI.

To run a scan:
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Nike", "official_domains": ["nike.com"]}'
```

## Option B: Local API Server

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn server:app --reload
```

Server runs at `http://localhost:8000`. Same request format as above.

## Option C: Local CLI

Edit `brand_input.json` with your target company, then instead of running the server, do:

```bash
python main.py
```

Output is written to `output/<company>_brand_profile.json`. Few sample brand profiles were generated and are present in the output folder.

## Run Tests

```bash
pip install -r requirements.txt
pytest -v
```