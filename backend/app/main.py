import logging
from contextlib import asynccontextmanager

from crawl4ai import AsyncWebCrawler, BrowserConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Crawl4AI browser on startup
    logger.info("Warming up Crawl4AI browser...")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        await crawler.awarmup()
    logger.info("Crawl4AI ready")
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
