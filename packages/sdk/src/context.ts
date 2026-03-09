/**
 * Gathers visitor context from the current page:
 * referrer, UTM parameters, URL, timestamp, viewport width.
 */
export function gatherContext() {
  const params = new URLSearchParams(window.location.search);

  return {
    referrer: document.referrer || "",
    url: window.location.href,
    utm_source: params.get("utm_source"),
    utm_medium: params.get("utm_medium"),
    utm_campaign: params.get("utm_campaign"),
    utm_content: params.get("utm_content"),
    utm_term: params.get("utm_term"),
    timestamp: new Date().toISOString(),
    viewport_width: window.innerWidth,
  };
}
