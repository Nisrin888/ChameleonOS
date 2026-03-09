/** SDK Configuration read from script tag attributes. */
export interface AOSConfig {
  publicKey: string;
  apiUrl: string;
  customSelectors: string;
}

/** Handshake request body sent to the API. */
export interface HandshakeRequest {
  public_key: string;
  session_id: string | null;
  context: {
    referrer: string;
    url: string;
    utm_source: string | null;
    utm_medium: string | null;
    utm_campaign: string | null;
    utm_content: string | null;
    utm_term: string | null;
    timestamp: string;
    viewport_width: number;
  };
}

/** Individual slot swap instruction from the API. */
export interface SlotPayload {
  slot_id: string;
  selector: string;
  action: "replace_text" | "replace_html" | "replace_src" | "replace_bg";
  value: string;
}

/** Handshake response from the API. */
export interface HandshakeResponse {
  session_id: string;
  variation_id: string;
  vibe: string;
  slots: SlotPayload[];
  ttl: number;
  is_control: boolean;
}

/** Tracking event sent to the API. */
export interface TrackEventPayload {
  session_id: string;
  public_key: string;
  event_type: string;
  event_name?: string;
  variation_id: string;
  slot_id?: string;
  metadata: Record<string, unknown>;
  timestamp: string;
}
