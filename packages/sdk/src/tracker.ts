import type { TrackEventPayload } from "./types";

let _apiUrl: string = "";
let _publicKey: string = "";
let _sessionId: string = "";
let _variationId: string = "";

export function initTracker(
  apiUrl: string,
  publicKey: string,
  sessionId: string,
  variationId: string
): void {
  _apiUrl = apiUrl;
  _publicKey = publicKey;
  _sessionId = sessionId;
  _variationId = variationId;
}

/**
 * Public API: AOS.track(eventType, metadata?)
 * Merchants call this to fire custom events (conversion, click, etc.)
 */
export function track(
  eventType: string,
  metadata: Record<string, unknown> = {}
): void {
  if (!_sessionId || !_publicKey) {
    console.warn("[AOS] SDK not initialized. Call init() first or wait for handshake.");
    return;
  }

  const event: TrackEventPayload = {
    session_id: _sessionId,
    public_key: _publicKey,
    event_type: eventType,
    variation_id: _variationId,
    metadata,
    timestamp: new Date().toISOString(),
  };

  // Use sendBeacon for reliability (survives page unload)
  const blob = new Blob([JSON.stringify(event)], {
    type: "application/json",
  });
  const sent = navigator.sendBeacon(`${_apiUrl}/v1/track`, blob);

  // Fallback to fetch if sendBeacon fails
  if (!sent) {
    fetch(`${_apiUrl}/v1/track`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(event),
      credentials: "omit",
      keepalive: true,
    }).catch(() => {
      // Silent fail — tracking is best-effort
    });
  }
}

/**
 * Auto-track all form submissions on the page.
 */
export function autoTrackForms(): void {
  document.addEventListener(
    "submit",
    (e) => {
      const form = e.target as HTMLFormElement;
      track("form_submit", {
        form_action: form.action || "",
        form_id: form.id || "",
      });
    },
    { capture: true }
  );
}

/**
 * Auto-track high-intent clicks (cart, checkout, CTA buttons).
 */
export function autoTrackClicks(): void {
  const selectors = [
    'a[href*="cart"]',
    'a[href*="checkout"]',
    'button[type="submit"]',
    ".add-to-cart",
    "[data-aos-track]",
  ];
  const combinedSelector = selectors.join(", ");

  document.addEventListener(
    "click",
    (e) => {
      const target = (e.target as Element).closest(combinedSelector);
      if (target) {
        track("click", {
          selector: describeElement(target),
          text: (target.textContent || "").trim().slice(0, 100),
          href: (target as HTMLAnchorElement).href || "",
        });
      }
    },
    { capture: true }
  );
}

function describeElement(el: Element): string {
  const tag = el.tagName.toLowerCase();
  const id = el.id ? `#${el.id}` : "";
  const cls = el.className
    ? `.${String(el.className).split(" ").filter(Boolean).join(".")}`
    : "";
  return `${tag}${id}${cls}`;
}
