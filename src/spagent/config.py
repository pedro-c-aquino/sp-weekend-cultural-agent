from pydantic import BaseModel
from pathlib import Path
import os, yaml


class Settings(BaseModel):
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1:8b-instruct"
    embeddings_model: str = "all-MiniLM-L6-v2"
    search_provider: str = "duckduckgo"
    persist_path: str = "data/vectordb"


def load_settings() -> Settings:
    cfg_path = Path("config/settings.yaml")
    data = yaml.safe_load(cfg_path.read_text())
    # simple env overlay
    data["llm"]["provider"] = os.getenv("LLM_PROVIDER", data["llm"]["provider"])
    data["llm"]["model"] = os.getenv("LLM_MODEL", data["llm"]["model"])
    data["embeddings"]["model"] = os.getenv(
        "EMBEDDINGS_MODEL", data["embeddings"]["model"]
    )
    data["search"]["provider"] = os.getenv(
        "SEARCH_PROVIDER", data["search"]["provider"]
    )
    return Settings(
        llm_provider=data["llm"]["provider"],
        llm_model=data["llm"]["model"],
        embeddings_model=data["embeddings"]["model"],
        search_provider=data["search"]["provider"],
        persist_path=data["retrieval"]["persist_path"],
    )
