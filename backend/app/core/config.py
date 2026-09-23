"""
Application configuration, loaded from environment variables.

Keeping this in one place makes it obvious in an interview exactly which
settings exist and what their defaults are. No secrets are hardcoded here;
values come from the environment (see .env.example).
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Which AI backend to use: "mock" (no API key needed) or "groq".
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")

    # Groq API key, only required when AI_PROVIDER=groq.
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Model name used when AI_PROVIDER=groq.
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Comma-separated list of origins allowed to call this API.
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")

    # How many previous conversation turns to forward to the AI layer.
    MAX_CONTEXT_TURNS: int = int(os.getenv("MAX_CONTEXT_TURNS", "4"))

    # Logging level.
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()
