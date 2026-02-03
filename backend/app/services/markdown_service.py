import re
from datetime import datetime, timezone


def build_front_matter(title: str, source_url: str) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "---\n"
        f"title: \"{title}\"\n"
        f"source: \"{source_url}\"\n"
        f"date: \"{date}\"\n"
        "---\n\n"
    )


def extract_title(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if match:
        return match.group(1).strip()
    lines = markdown.strip().splitlines()
    if lines:
        return lines[0].strip()[:120]
    return "Untitled"


def clean_markdown(raw: str) -> str:
    text = raw

    # Remove empty links: [](url) or [text]()
    text = re.sub(r"\[([^\]]*)\]\(\s*\)", r"\1", text)
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)

    # Remove image-only lines that are likely icons/avatars (very short alt text)
    text = re.sub(r"^!\[.{0,3}\]\([^)]+\)\s*$", "", text, flags=re.MULTILINE)

    # Remove lines that are only links with no descriptive text (navigation remnants)
    text = re.sub(r"^\s*\[?\s*[→←▸▶►▹›‹«»]\s*\]?\s*$", "", text, flags=re.MULTILINE)

    # Remove common noise patterns
    text = re.sub(r"^\s*Skip to (?:main )?content\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*(?:Share|Tweet|Pin|Email)\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:Previous|Next)\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # Remove horizontal rules that appear more than twice in a row
    text = re.sub(r"(---\n){3,}", "---\n\n", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    text = text.strip()
    return text


def process_markdown(raw_markdown: str, source_url: str) -> str:
    cleaned = clean_markdown(raw_markdown)
    title = extract_title(cleaned)
    front_matter = build_front_matter(title, source_url)
    return front_matter + cleaned
