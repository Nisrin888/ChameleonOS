"""
Referrer page fetcher for background enrichment.
Fetches a referrer URL and extracts text/metadata for vibe analysis.
"""
import httpx

MAX_CONTENT_LENGTH = 5000  # Characters to extract from page
FETCH_TIMEOUT = 10  # Seconds


async def fetch_referrer_page(url: str) -> str | None:
    """
    Fetch a referrer page and extract readable text content.
    Returns None if the page can't be fetched.
    """
    try:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AOS-Bot/1.0; +https://aos.dev)",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None

            html = response.text

            # Basic HTML text extraction (no heavy dependencies)
            text = _extract_text_from_html(html)
            return text[:MAX_CONTENT_LENGTH] if text else None

    except Exception:
        return None


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML. Basic implementation without BeautifulSoup."""
    import re

    # Remove script and style elements
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        text,
        re.IGNORECASE,
    )
    description = desc_match.group(1).strip() if desc_match else ""

    # Extract h1-h3 headings
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", text, re.IGNORECASE | re.DOTALL)
    headings_text = " | ".join(re.sub(r"<[^>]+>", "", h).strip() for h in headings[:5])

    # Remove all remaining HTML tags
    body_text = re.sub(r"<[^>]+>", " ", text)
    body_text = re.sub(r"\s+", " ", body_text).strip()

    parts = []
    if title:
        parts.append(f"Title: {title}")
    if description:
        parts.append(f"Description: {description}")
    if headings_text:
        parts.append(f"Headings: {headings_text}")
    parts.append(f"Content: {body_text[:2000]}")

    return "\n".join(parts)
