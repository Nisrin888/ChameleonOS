import type { AOSConfig } from "./types";

/**
 * Reads SDK configuration from the <script> tag attributes.
 * Looks for: data-key, data-api-url, data-selectors
 */
export function readConfig(): AOSConfig {
  // Find the script tag that loaded us
  const script =
    (document.currentScript as HTMLScriptElement) ||
    (document.querySelector("script[data-key]") as HTMLScriptElement);

  if (!script) {
    throw new Error("[AOS] Script tag not found. Ensure data-key is set.");
  }

  const publicKey = script.getAttribute("data-key");
  if (!publicKey) {
    throw new Error("[AOS] Missing data-key attribute on script tag.");
  }

  const apiUrl =
    script.getAttribute("data-api-url") || "http://localhost:8000";
  const customSelectors = script.getAttribute("data-selectors") || "";

  return { publicKey, apiUrl, customSelectors };
}
