from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

from app.api.models import CrawlMode, TaskStatus
from app.core.config import settings
from app.core.crawler import crawl_url, crawl_url_with_html
from app.services.gemini_service import GeminiNavigationAnalyzer
from app.services.markdown_service import process_markdown
from app.services.sitemap_service import fetch_sitemap_urls
from app.services.task_service import task_store

logger = logging.getLogger(__name__)


async def _crawl_single(
    semaphore: asyncio.Semaphore,
    page_url: str,
    cookies: list[dict] | None = None,
) -> str | None:
    async with semaphore:
        try:
            raw = await crawl_url(page_url, cookies=cookies)
            return process_markdown(raw, page_url)
        except Exception:
            logger.warning("Failed to crawl %s, skipping", page_url)
            return None


async def _smart_crawl(
    task_id: str,
    start_url: str,
    path_prefix: str | None,
    max_pages: int,
    gemini_api_key: str,
    gemini_model: str,
    cookies: list[dict] | None = None,
) -> str:
    """Smart crawl using Gemini to discover navigation links."""
    analyzer = GeminiNavigationAnalyzer(gemini_api_key, gemini_model)

    # Track visited URLs
    visited: set[str] = set()
    to_visit: list[str] = [start_url]
    results: list[str] = []

    # Determine path prefix from start URL if not provided
    if not path_prefix:
        parsed = urlparse(start_url)
        # Use the path up to the last segment as prefix
        path_parts = parsed.path.rsplit("/", 1)
        path_prefix = path_parts[0] if len(path_parts) > 1 else "/"

    task_store.update_progress(task_id, 0, max_pages)

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)

        # Skip if already visited
        normalized_url = current_url.rstrip("/")
        if normalized_url in visited:
            continue

        visited.add(normalized_url)
        logger.info("Smart crawl: processing %s (%d/%d)", current_url, len(visited), max_pages)

        try:
            # Crawl page and get both markdown and HTML
            markdown, html = await crawl_url_with_html(current_url, cookies=cookies)

            if markdown:
                processed = process_markdown(markdown, current_url)
                results.append(processed)

            # Analyze HTML with Gemini to find navigation links
            if html and len(visited) < max_pages:
                analysis = await analyzer.analyze_page(html, current_url, path_prefix)

                for link in analysis.get("navigation_links", []):
                    link_url = link.get("url", "").rstrip("/")
                    if link_url and link_url not in visited and link_url not in to_visit:
                        to_visit.append(link_url)
                        logger.debug("Discovered link: %s (%s)", link_url, link.get("type"))

        except Exception as e:
            logger.warning("Failed to process %s: %s", current_url, e)

        task_store.update_progress(task_id, len(visited), min(len(visited) + len(to_visit), max_pages))

    if not results:
        raise RuntimeError("No pages successfully crawled")

    # Update final progress
    task_store.update_progress(task_id, len(results), len(results))

    return "\n\n---\n\n".join(results)


async def run_crawl_task(
    task_id: str,
    url: str,
    mode: CrawlMode,
    cookies: list[dict] | None = None,
    path_prefix: str | None = None,
    max_pages: int = 50,
    gemini_api_key: str | None = None,
    gemini_model: str = "gemini-2.5-flash",
) -> None:
    task_store.update_status(task_id, TaskStatus.PROCESSING)

    try:
        if mode == CrawlMode.SMART:
            # Use Gemini API key from request or env
            api_key = gemini_api_key or settings.gemini_api_key
            if not api_key:
                raise RuntimeError("Gemini API key required for smart mode. Set GEMINI_API_KEY env var or provide in request.")

            result = await _smart_crawl(
                task_id=task_id,
                start_url=url,
                path_prefix=path_prefix,
                max_pages=max_pages,
                gemini_api_key=api_key,
                gemini_model=gemini_model,
                cookies=cookies,
            )

        elif mode == CrawlMode.SITEMAP:
            urls = await fetch_sitemap_urls(url)
            if not urls:
                raise RuntimeError("No URLs found in sitemap")

            total = len(urls)
            task_store.update_progress(task_id, 0, total)

            semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)
            parts: list[str] = []
            processed = 0

            batch_size = settings.max_concurrent_tasks
            for i in range(0, total, batch_size):
                batch = urls[i : i + batch_size]
                tasks = [_crawl_single(semaphore, u, cookies) for u in batch]
                batch_results = await asyncio.gather(*tasks)

                for md in batch_results:
                    processed += 1
                    if md:
                        parts.append(md)

                task_store.update_progress(task_id, processed, total)

            if not parts:
                raise RuntimeError("All sitemap URLs failed to crawl")
            result = "\n\n---\n\n".join(parts)

        else:  # SINGLE mode
            task_store.update_progress(task_id, 0, 1)
            raw = await crawl_url(url, cookies=cookies)
            result = process_markdown(raw, url)

        task_store.set_result(task_id, result)

    except Exception as exc:
        logger.exception("Crawl task %s failed", task_id)
        task_store.set_error(task_id, str(exc))
