from enum import Enum
from typing import Literal

from pydantic import BaseModel, HttpUrl


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlMode(str, Enum):
    SINGLE = "single"
    SITEMAP = "sitemap"
    SMART = "smart"


class CookieItem(BaseModel):
    name: str
    value: str
    domain: str = ""
    path: str = "/"


class CrawlRequest(BaseModel):
    url: HttpUrl
    mode: CrawlMode = CrawlMode.SINGLE
    # Legacy field for backward compatibility
    sitemap: bool = False
    cookies: list[CookieItem] = []
    # Smart mode options
    path_prefix: str | None = None
    max_pages: int = 50
    gemini_api_key: str | None = None  # Uses env var if not provided
    gemini_model: str = "gemini-2.5-flash"


class CrawlResponse(BaseModel):
    task_id: str
    status: TaskStatus


class TaskResult(BaseModel):
    id: str
    url: str
    status: TaskStatus
    progress: int = 0
    total_pages: int = 0
    processed_pages: int = 0
    result: str | None = None
    error: str | None = None


class DriveUploadRequest(BaseModel):
    task_id: str
    access_token: str
    filename: str | None = None


class DriveUploadResponse(BaseModel):
    file_id: str
    name: str
    web_link: str


class HealthResponse(BaseModel):
    status: str = "ok"
