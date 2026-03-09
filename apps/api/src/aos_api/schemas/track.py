from pydantic import BaseModel


class TrackEventRequest(BaseModel):
    public_key: str
    session_id: str
    event_type: str  # impression, click, conversion, form_submit, custom
    event_name: str | None = None
    variation_id: str
    slot_id: str | None = None
    metadata: dict | None = None
    timestamp: str = ""


class TrackEventResponse(BaseModel):
    status: str = "ok"
