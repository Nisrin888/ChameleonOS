/**
 * CORS handling with origin validation.
 * In dev: allows all localhost origins.
 * In production: validates against per-tenant allowed_origins (future).
 */

export function validateOrigin(origin: string | null, env: string): boolean {
  if (env === "development") {
    if (!origin) return true;
    return (
      origin.startsWith("http://localhost") ||
      origin.startsWith("http://127.0.0.1") ||
      origin.startsWith("file://")
    );
  }
  // Production: would check against tenant's allowed_origins
  return !!origin;
}

export function corsHeaders(
  origin: string | null,
  env: string
): Record<string, string> {
  const allowed = validateOrigin(origin, env) ? origin || "*" : "";
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

export function handlePreflight(
  origin: string | null,
  env: string
): Response {
  return new Response(null, {
    status: 204,
    headers: corsHeaders(origin, env),
  });
}
