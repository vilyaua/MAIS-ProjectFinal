"""Settings for the Dev Team multi-agent system. Prompts loaded from Langfuse."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

APP_VERSION = (Path(__file__).parent / "VERSION").read_text().strip()


class Settings(BaseSettings):
    """App configuration loaded from .env (via pydantic-settings)."""

    app_name: str = "AI Dev Team — Final Project"
    openai_api_key: SecretStr
    model_powerful: str = "openai:gpt-5.5"
    model_mid: str = "openai:gpt-5.4"
    model_fast: str = "openai:gpt-4.1-mini"

    # Langfuse
    langfuse_secret_key: SecretStr | None = None
    langfuse_public_key: str | None = None
    langfuse_base_url: str = "https://us.cloud.langfuse.com"

    # Web search
    max_search_results: int = 5
    max_search_content_length: int = 3000
    max_url_content_length: int = 8000

    # RAG
    embedding_model: str = "text-embedding-3-small"
    data_dir: str = "data"
    index_dir: str = "index"
    chunk_size: int = 500
    chunk_overlap: int = 100
    retrieval_top_k: int = 10
    rerank_top_n: int = 3

    # Agent
    workspace_dir: str = "workspace"
    output_dir: str = "output"
    max_qa_iterations: int = 5
    repl_timeout: int = 30

    # Notion integration (optional)
    notion_token: SecretStr | None = None

    # GitHub integration (optional)
    github_token: SecretStr | None = None
    github_repo: str | None = None  # e.g. "vilyaua/MAIS-ProjectFinal"
    github_base_branch: str = "main"

    model_config = {"env_file": ".env"}
