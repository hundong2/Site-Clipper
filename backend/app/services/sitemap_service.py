from urllib.parse import urlparse

import httpx
import xml.etree.ElementTree as ET


SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


async def fetch_sitemap_urls(base_url: str) -> list[str]:
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(sitemap_url)
        resp.raise_for_status()

    root = ET.fromstring(resp.text)

    # Handle sitemap index (nested sitemaps)
    sitemap_locs = root.findall(".//sm:sitemap/sm:loc", SITEMAP_NS)
    if sitemap_locs:
        urls: list[str] = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for loc in sitemap_locs:
                sub_resp = await client.get(loc.text)
                if sub_resp.is_success:
                    sub_root = ET.fromstring(sub_resp.text)
                    urls.extend(
                        u.text
                        for u in sub_root.findall(".//sm:url/sm:loc", SITEMAP_NS)
                        if u.text
                    )
        return urls

    # Standard sitemap
    return [
        u.text
        for u in root.findall(".//sm:url/sm:loc", SITEMAP_NS)
        if u.text
    ]
