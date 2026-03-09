import type { AOSConfig, HandshakeRequest, HandshakeResponse } from "./types";
import { gatherContext } from "./context";
import { getSessionId, setSessionId, setVariationId } from "./session";

/**
 * Performs the handshake with the AOS API.
 * Sends visitor context, receives variation payload.
 */
export async function performHandshake(
  config: AOSConfig
): Promise<HandshakeResponse> {
  const context = gatherContext();
  const sessionId = getSessionId();

  const body: HandshakeRequest = {
    public_key: config.publicKey,
    session_id: sessionId,
    context,
  };

  const response = await fetch(`${config.apiUrl}/v1/handshake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "omit", // No cookies
  });

  if (!response.ok) {
    throw new Error(`[AOS] Handshake failed: ${response.status}`);
  }

  const payload: HandshakeResponse = await response.json();

  // Persist session for subsequent page loads
  setSessionId(payload.session_id);
  setVariationId(payload.variation_id);

  return payload;
}
