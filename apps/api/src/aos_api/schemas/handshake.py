from pydantic import BaseModel


class VisitorContext(BaseModel):
    referrer: str = ""
    url: str = ""
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    timestamp: str = ""
    viewport_width: int | None = None
    geo_country: str | None = None


class HandshakeRequest(BaseModel):
    public_key: str
    context: VisitorContext
    session_id: str | None = None


class SlotVariationResponse(BaseModel):
    slot_id: str
    selector: str
    action: str
    value: str


class HandshakeResponse(BaseModel):
    session_id: str
    variation_id: str
    vibe: str
    slots: list[SlotVariationResponse]
    ttl: int = 86400
    is_control: bool = False
