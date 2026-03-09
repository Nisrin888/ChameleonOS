"""
Rule-based vibe classifier.
Maps known referrer domains and UTM parameters to VibeSegments.
This is the "fast path" — no LLM call, <1ms.

Priority order:
  1. UTM campaign keywords (most specific signal)
  2. UTM source mapping
  3. Referrer domain mapping
  4. Fallback to "default"
"""
from urllib.parse import urlparse

from aos_api.schemas.handshake import VisitorContext


DOMAIN_VIBE_MAP: dict[str, str] = {
    "tiktok.com": "casual",
    "instagram.com": "bold",
    "pinterest.com": "minimalist",
    "pinterest.ca": "minimalist",
    "pinterest.co.uk": "minimalist",
    "linkedin.com": "professional",
    "twitter.com": "edgy",
    "x.com": "edgy",
    "facebook.com": "casual",
    "google.com": "default",
    "youtube.com": "casual",
    "reddit.com": "edgy",
}

UTM_SOURCE_VIBE_MAP: dict[str, str] = {
    "ig": "bold",
    "instagram": "bold",
    "tiktok": "casual",
    "tt": "casual",
    "pinterest": "minimalist",
    "pin": "minimalist",
    "linkedin": "professional",
    "li": "professional",
    "email": "professional",
    "newsletter": "professional",
    "facebook": "casual",
    "fb": "casual",
    "twitter": "edgy",
    "x": "edgy",
    "reddit": "edgy",
    "youtube": "casual",
    "yt": "casual",
}

UTM_CAMPAIGN_KEYWORDS: dict[str, str] = {
    "luxury": "luxe",
    "premium": "luxe",
    "elegant": "luxe",
    "sport": "athletic",
    "fitness": "athletic",
    "gym": "athletic",
    "workout": "athletic",
    "wellness": "wellness",
    "zen": "wellness",
    "calm": "wellness",
    "mindful": "wellness",
    "bold": "bold",
    "loud": "bold",
    "neon": "bold",
    "minimal": "minimalist",
    "clean": "minimalist",
    "quiet": "minimalist",
    "simple": "minimalist",
    "professional": "professional",
    "business": "professional",
    "corporate": "professional",
    "edgy": "edgy",
    "punk": "edgy",
    "street": "edgy",
}


def classify(context: VisitorContext) -> str:
    """Classify visitor vibe from context signals. Returns a VibeSegment string."""

    # Priority 1: UTM campaign keywords (most specific signal)
    if context.utm_campaign:
        campaign_lower = context.utm_campaign.lower()
        for keyword, vibe in UTM_CAMPAIGN_KEYWORDS.items():
            if keyword in campaign_lower:
                return vibe

    # Priority 2: UTM source
    if context.utm_source:
        vibe = UTM_SOURCE_VIBE_MAP.get(context.utm_source.lower())
        if vibe:
            return vibe

    # Priority 3: Referrer domain
    if context.referrer:
        try:
            domain = urlparse(context.referrer).hostname or ""
            domain = domain.removeprefix("www.")
            vibe = DOMAIN_VIBE_MAP.get(domain)
            if vibe:
                return vibe
        except Exception:
            pass

    # Priority 4: UTM medium hints
    if context.utm_medium:
        medium = context.utm_medium.lower()
        if medium in ("social", "social-media"):
            return "casual"
        if medium in ("email", "newsletter"):
            return "professional"

    return "default"
