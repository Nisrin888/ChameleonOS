/**
 * Adaptive-OS Edge Middleware — Cloudflare Worker
 *
 * Acts as an API gateway between the SDK and FastAPI backend.
 * - Validates request origins (CORS)
 * - Enriches requests with geo-location data from CF headers
 * - Proxies /v1/handshake and /v1/track to the backend
 * - Serves the SDK bundle at /sdk.js
 */
import type { Env } from "./types";
import { validateOrigin, corsHeaders, handlePreflight } from "./cors";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin");
    const cors = corsHeaders(origin, env.ENVIRONMENT);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return handlePreflight(origin, env.ENVIRONMENT);
    }

    // Origin validation
    if (
      request.method === "POST" &&
      !validateOrigin(origin, env.ENVIRONMENT)
    ) {
      return jsonResponse({ error: "Origin not allowed" }, 403, cors);
    }

    const path = url.pathname;

    // --- Route: /v1/handshake ---
    if (path === "/v1/handshake" && request.method === "POST") {
      return proxyToBackend(request, "/v1/handshake", env, cors);
    }

    // --- Route: /v1/track ---
    if (path === "/v1/track" && request.method === "POST") {
      return proxyToBackend(request, "/v1/track", env, cors);
    }

    // --- Route: /v1/dashboard/* ---
    if (path.startsWith("/v1/dashboard")) {
      return proxyToBackend(request, path + url.search, env, cors);
    }

    // --- Route: /health ---
    if (path === "/health") {
      return jsonResponse(
        { status: "ok", service: "aos-edge" },
        200,
        cors
      );
    }

    // --- 404 ---
    return jsonResponse({ error: "Not found" }, 404, cors);
  },
};

/**
 * Proxy a request to the FastAPI backend, enriching with geo data.
 */
async function proxyToBackend(
  request: Request,
  path: string,
  env: Env,
  cors: Record<string, string>
): Promise<Response> {
  const backendUrl = `${env.AOS_API_URL}${path}`;

  // Extract Cloudflare geo data
  const cf = (request as any).cf;
  const geoCountry = cf?.country || "";
  const geoCity = cf?.city || "";

  // Forward the request
  const body = request.method === "POST" ? await request.text() : undefined;

  // Enrich POST body with geo data
  let enrichedBody = body;
  if (body && geoCountry) {
    try {
      const parsed = JSON.parse(body);
      if (parsed.context) {
        parsed.context.geo_country = geoCountry;
      }
      enrichedBody = JSON.stringify(parsed);
    } catch {
      // Not JSON, send as-is
    }
  }

  try {
    const backendResponse = await fetch(backendUrl, {
      method: request.method,
      headers: {
        "Content-Type": "application/json",
        "X-Forwarded-For":
          request.headers.get("CF-Connecting-IP") || "",
        "X-AOS-Geo-Country": geoCountry,
        "X-AOS-Geo-City": geoCity,
      },
      body: enrichedBody,
    });

    const responseBody = await backendResponse.text();

    return new Response(responseBody, {
      status: backendResponse.status,
      headers: {
        "Content-Type": "application/json",
        ...cors,
      },
    });
  } catch (error) {
    console.error("[AOS Edge] Backend proxy error:", error);
    return jsonResponse(
      { error: "Backend unavailable" },
      502,
      cors
    );
  }
}

function jsonResponse(
  data: unknown,
  status: number,
  cors: Record<string, string>
): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...cors },
  });
}
