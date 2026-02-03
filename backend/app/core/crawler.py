from __future__ import annotations

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from app.core.config import settings

EXCLUDED_TAGS = [
    "nav", "footer", "header", "aside",
    "script", "style", "noscript",
    "iframe", "form",
]

EXCLUDED_SELECTORS = [
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    "[class*='sidebar']",
    "[class*='menu']",
    "[class*='nav']",
    "[class*='footer']",
    "[class*='header']",
    "[class*='cookie']",
    "[class*='popup']",
    "[class*='modal']",
    "[class*='ad-']",
    "[class*='ads']",
    "[class*='advertisement']",
    "[id*='sidebar']",
    "[id*='footer']",
    "[id*='header']",
    "[id*='cookie']",
    "[id*='ad-']",
]


async def crawl_url(
    url: str,
    cookies: list[dict] | None = None,
) -> str:
    browser_config = BrowserConfig(
        headless=True,
        cookies=cookies or [],
    )
    run_config = CrawlerRunConfig(
        excluded_tags=EXCLUDED_TAGS,
        excluded_selector=",".join(EXCLUDED_SELECTORS),
        word_count_threshold=10,
        remove_forms=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config,
            timeout=settings.crawl_timeout,
        )

        if not result.success:
            raise RuntimeError(f"Crawl failed: {result.error_message}")

        return result.fit_markdown or result.markdown


async def crawl_url_with_html(
    url: str,
    cookies: list[dict] | None = None,
) -> tuple[str, str]:
    """Crawl URL and return both markdown and raw HTML."""
    browser_config = BrowserConfig(
        headless=True,
        cookies=cookies or [],
    )
    run_config = CrawlerRunConfig(
        excluded_tags=EXCLUDED_TAGS,
        excluded_selector=",".join(EXCLUDED_SELECTORS),
        word_count_threshold=10,
        remove_forms=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config,
            timeout=settings.crawl_timeout,
        )

        if not result.success:
            raise RuntimeError(f"Crawl failed: {result.error_message}")

        markdown = result.fit_markdown or result.markdown
        html = result.html or ""

        return markdown, html
