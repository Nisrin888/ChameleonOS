#!/bin/bash
# End-to-end test script for Adaptive-OS.
# Run with: ./scripts/test-e2e.sh
# Requires: API running on localhost:8000 with seeded database.

set -e

API_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass() { echo -e "  ${GREEN}PASS${NC} $1"; }
fail() { echo -e "  ${RED}FAIL${NC} $1"; exit 1; }

echo "============================================"
echo "  Adaptive-OS — End-to-End Tests"
echo "============================================"
echo ""

# --- Test 1: Health check ---
echo "[Test 1] Health check"
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | grep -q '"ok"' && pass "API is healthy" || fail "API not responding"

# --- Test 2: Handshake with TikTok referrer → casual vibe ---
echo "[Test 2] Handshake — TikTok traffic → casual vibe"
RESPONSE=$(curl -s -X POST "$API_URL/v1/handshake" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "pk_demo_001",
    "context": {
      "referrer": "https://tiktok.com/@username/video/123",
      "url": "http://localhost:3000/",
      "timestamp": "2026-02-27T12:00:00Z"
    }
  }')
echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['vibe']=='casual', f'Expected casual, got {d[\"vibe\"]}'" 2>/dev/null \
  && pass "Vibe = casual" || fail "Expected casual vibe. Response: $RESPONSE"
SESSION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)
VARIATION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['variation_id'])" 2>/dev/null)
echo "     Session: $SESSION_ID"
echo "     Variation: $VARIATION_ID"

# --- Test 3: Handshake with Pinterest UTM → minimalist vibe ---
echo "[Test 3] Handshake — Pinterest UTM → minimalist vibe"
RESPONSE2=$(curl -s -X POST "$API_URL/v1/handshake" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "pk_demo_001",
    "context": {
      "referrer": "",
      "url": "http://localhost:3000/?utm_source=pinterest",
      "utm_source": "pinterest",
      "timestamp": "2026-02-27T12:00:00Z"
    }
  }')
echo "$RESPONSE2" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['vibe']=='minimalist', f'Expected minimalist, got {d[\"vibe\"]}'" 2>/dev/null \
  && pass "Vibe = minimalist" || fail "Expected minimalist vibe. Response: $RESPONSE2"

# --- Test 4: Handshake with IG UTM → bold vibe ---
echo "[Test 4] Handshake — Instagram UTM → bold vibe"
RESPONSE3=$(curl -s -X POST "$API_URL/v1/handshake" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "pk_demo_001",
    "context": {
      "referrer": "",
      "url": "http://localhost:3000/?utm_source=ig",
      "utm_source": "ig",
      "timestamp": "2026-02-27T12:00:00Z"
    }
  }')
echo "$RESPONSE3" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['vibe']=='bold', f'Expected bold, got {d[\"vibe\"]}'" 2>/dev/null \
  && pass "Vibe = bold" || fail "Expected bold vibe. Response: $RESPONSE3"

# --- Test 5: Session stickiness ---
echo "[Test 5] Session stickiness — same session_id → same variation"
RESPONSE4=$(curl -s -X POST "$API_URL/v1/handshake" \
  -H "Content-Type: application/json" \
  -d "{
    \"public_key\": \"pk_demo_001\",
    \"session_id\": \"$SESSION_ID\",
    \"context\": {
      \"referrer\": \"https://pinterest.com/\",
      \"url\": \"http://localhost:3000/\",
      \"timestamp\": \"2026-02-27T12:01:00Z\"
    }
  }")
RETURNED_SESSION=$(echo "$RESPONSE4" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)
[ "$RETURNED_SESSION" = "$SESSION_ID" ] \
  && pass "Session persisted (same session_id returned)" || fail "Session not sticky"

# --- Test 6: Track conversion event ---
echo "[Test 6] Track conversion event"
TRACK_RESPONSE=$(curl -s -X POST "$API_URL/v1/track" \
  -H "Content-Type: application/json" \
  -d "{
    \"public_key\": \"pk_demo_001\",
    \"session_id\": \"$SESSION_ID\",
    \"event_type\": \"conversion\",
    \"variation_id\": \"$VARIATION_ID\",
    \"slot_id\": \"hero-headline\",
    \"timestamp\": \"2026-02-27T12:02:00Z\"
  }")
echo "$TRACK_RESPONSE" | grep -q '"ok"' \
  && pass "Conversion event recorded" || fail "Track failed. Response: $TRACK_RESPONSE"

# --- Test 7: Invalid public key ---
echo "[Test 7] Invalid public key → 404"
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_URL/v1/handshake" \
  -H "Content-Type: application/json" \
  -d '{"public_key": "pk_invalid", "context": {"referrer": "", "url": "", "timestamp": ""}}')
[ "$HTTP_CODE" = "404" ] \
  && pass "Returns 404 for invalid key" || fail "Expected 404, got $HTTP_CODE"

# --- Test 8: Dashboard API ---
echo "[Test 8] Dashboard performance endpoint"
sleep 1  # Wait for background tasks to persist
DASH_RESPONSE=$(curl -s "$API_URL/v1/dashboard/performance?public_key=pk_demo_001")
echo "$DASH_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'summary' in d and 'rows' in d" 2>/dev/null \
  && pass "Dashboard returns summary + rows" || fail "Dashboard response invalid. Response: $DASH_RESPONSE"

echo ""
echo "============================================"
echo -e "  ${GREEN}All tests passed!${NC}"
echo "============================================"
