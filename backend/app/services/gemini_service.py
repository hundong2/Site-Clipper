import json
import google.generativeai as genai
from urllib.parse import urljoin, urlparse

NAVIGATION_PROMPT = """Analyze this HTML page and extract navigation links.

The base URL of this page is: {base_url}

1. **Navigation links**: Find links that are part of the documentation structure:
   - "Next", "Previous", "Continue" buttons or links
   - Sidebar/menu links to other documentation pages
   - Table of contents (TOC) links
   - Pagination links

2. **Main content selector**: Identify the CSS selector for the main content area

Return JSON only, no markdown:
{{
  "navigation_links": [
    {{"url": "relative/path.html", "text": "link text", "type": "next|prev|menu|toc"}}
  ],
  "content_selector": "CSS selector for main content",
  "page_title": "extracted title"
}}

Rules:
- Only include links that are part of documentation (not external links, social media, ads, etc.)
- IMPORTANT: Return URLs exactly as they appear in the href attribute (relative paths like "appetite.html" or "../page.html")
- Do NOT convert relative URLs to absolute URLs
- If no navigation found, return empty array

HTML:
"""


class GeminiNavigationAnalyzer:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def analyze_page(self, html: str, base_url: str, path_prefix: str | None = None) -> dict:
        """Analyze HTML page and extract navigation links."""
        # Truncate HTML if too long (keep first 100k chars)
        truncated_html = html[:100000] if len(html) > 100000 else html

        prompt = NAVIGATION_PROMPT.format(base_url=base_url) + truncated_html

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )

            result = json.loads(response.text)

            # Filter links by path prefix if specified
            if path_prefix and result.get("navigation_links"):
                parsed_base = urlparse(base_url)
                base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

                filtered_links = []
                for link in result["navigation_links"]:
                    url = link.get("url", "")
                    # Make URL absolute if relative
                    if url.startswith("/"):
                        url = base_domain + url
                    elif not url.startswith("http"):
                        url = urljoin(base_url, url)

                    link["url"] = url

                    # Check if URL matches prefix
                    if self._matches_prefix(url, base_domain, path_prefix):
                        filtered_links.append(link)

                result["navigation_links"] = filtered_links

            return result

        except Exception as e:
            return {
                "navigation_links": [],
                "content_selector": None,
                "page_title": None,
                "error": str(e)
            }

    def _matches_prefix(self, url: str, base_domain: str, path_prefix: str) -> bool:
        """Check if URL matches the base domain and path prefix."""
        parsed = urlparse(url)
        url_domain = f"{parsed.scheme}://{parsed.netloc}"

        if url_domain != base_domain:
            return False

        if path_prefix:
            # Normalize prefix
            prefix = path_prefix.rstrip("/")
            path = parsed.path.rstrip("/")
            return path.startswith(prefix)

        return True
