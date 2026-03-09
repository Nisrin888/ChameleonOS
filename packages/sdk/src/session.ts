/**
 * Session ID management via sessionStorage.
 * No cookies. Session persists across page navigations within the same tab.
 */
const SESSION_KEY = "aos_session_id";
const VARIATION_KEY = "aos_variation_id";

export function getSessionId(): string | null {
  try {
    return sessionStorage.getItem(SESSION_KEY);
  } catch {
    return null; // sessionStorage blocked (e.g. private mode)
  }
}

export function setSessionId(id: string): void {
  try {
    sessionStorage.setItem(SESSION_KEY, id);
  } catch {
    // Silently fail
  }
}

export function getVariationId(): string | null {
  try {
    return sessionStorage.getItem(VARIATION_KEY);
  } catch {
    return null;
  }
}

export function setVariationId(id: string): void {
  try {
    sessionStorage.setItem(VARIATION_KEY, id);
  } catch {
    // Silently fail
  }
}
