from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Site Clipper API"
    debug: bool = False
    allowed_origins: list[str] = ["*"]
    crawl_timeout: int = 60
    max_concurrent_tasks: int = 10

    # Gemini API (uses GEMINI_API_KEY env var directly)
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    model_config = {
        "env_prefix": "CLIPPER_",
        "populate_by_name": True,
    }


settings = Settings()
