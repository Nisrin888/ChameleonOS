// ============================================================
// Adaptive-OS Shared Types
// Contract between SDK, Edge Worker, Dashboard, and API.
// ============================================================

// === Visitor Context ===

export interface VisitorContext {
  referrer: string;
  url: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  timestamp: string; // ISO 8601
  viewport_width?: number;
  geo_country?: string; // Populated by edge or API from IP
}

// === Handshake (SDK -> API -> SDK) ===

export interface HandshakeRequest {
  public_key: string;
  context: VisitorContext;
  session_id?: string; // undefined on first visit
}

export interface HandshakeResponse {
  session_id: string;
  variation_id: string; // UUID for attribution
  vibe: string; // The classified vibe segment
  slots: SlotVariation[];
  ttl: number; // seconds until re-handshake
  is_control: boolean; // Whether this is the control group
}

export interface SlotVariation {
  slot_id: string; // e.g. "hero-headline"
  selector: string; // CSS selector or data-aos-slot value
  action: SlotAction;
  value: string; // The new content/URL
}

export type SlotAction =
  | "replace_text"
  | "replace_html"
  | "replace_src"
  | "replace_bg";

// === Variation Content (stored in DB) ===

export interface VariationContent {
  headline?: string;
  subheadline?: string;
  image_url?: string;
  cta_text?: string;
  cta_url?: string;
  custom?: Record<string, string>; // For arbitrary slot content
}

// === Event Tracking (SDK -> API) ===

export interface TrackEvent {
  public_key: string;
  session_id: string;
  event_type: EventType;
  event_name?: string; // For custom events
  variation_id: string;
  slot_id?: string;
  metadata?: Record<string, unknown>;
  timestamp: string; // ISO 8601
}

export type EventType =
  | "impression"
  | "click"
  | "conversion"
  | "form_submit"
  | "custom";

// === Vibe Segments ===

export type VibeSegment =
  | "minimalist"
  | "bold"
  | "luxe"
  | "casual"
  | "professional"
  | "wellness"
  | "athletic"
  | "edgy"
  | "default";

// === Dashboard Types ===

export interface DashboardSummary {
  total_impressions: number;
  total_conversions: number;
  overall_cvr: number; // 0.0 - 1.0
  control_cvr: number; // 0.0 - 1.0
  lift_vs_control: number; // percentage, e.g. 15.3 means +15.3%
}

export interface PerformanceRow {
  traffic_source: string; // e.g. "tiktok", "pinterest", "google"
  vibe: string;
  variation_name: string;
  variation_id: string;
  impressions: number;
  conversions: number;
  cvr: number; // 0.0 - 1.0
  is_control: boolean;
}

export interface DashboardData {
  summary: DashboardSummary;
  rows: PerformanceRow[];
  last_updated: string; // ISO timestamp
}

// === Tenant (internal) ===

export interface TenantConfig {
  id: string;
  name: string;
  public_key: string;
  allowed_origins: string[];
}

// === Constants ===

export const AOS_HANDSHAKE_PATH = "/v1/handshake";
export const AOS_TRACK_PATH = "/v1/track";
export const AOS_DASHBOARD_PREFIX = "/v1/dashboard";
export const SESSION_TTL_SECONDS = 86400; // 24 hours
export const CONTROL_GROUP_PERCENTAGE = 0.10; // 10%
export const MAX_VARIATIONS_PER_SLOT = 3;
