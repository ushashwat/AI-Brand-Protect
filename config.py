"""Centralised application settings."""

import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key: str = os.getenv("OPENAI_API_KEY")
openai_model: str = os.getenv("OPENAI_MODEL")
openai_base_url: str = os.getenv("OPENAI_BASE_URL")

tavily_api_key: str = os.getenv("TAVILY_API_KEY")

request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "15"))
