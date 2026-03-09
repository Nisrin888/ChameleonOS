/**
 * Adaptive-OS SDK
 *
 * Platform-agnostic script tag for dynamic content personalization.
 * Usage: <script src="aos.js" data-key="pk_abc123" data-api-url="https://api.aos.dev"></script>
 *
 * Lifecycle:
 * 1. Inject CSS guard (hide targeted slots)
 * 2. Gather visitor context (referrer, UTMs, viewport)
 * 3. POST /v1/handshake to get variation payload
 * 4. Swap content in targeted DOM slots
 * 5. Reveal slots (opacity transition)
 * 6. Set up auto-tracking (forms, high-intent clicks)
 * 7. Expose AOS.track() for custom events
 */

import { readConfig } from "./config";
import { injectGuard, revealSlots, removeGuard } from "./guard";
import { performHandshake } from "./handshake";
import { renderSlots } from "./renderer";
import { initTracker, track, autoTrackForms, autoTrackClicks } from "./tracker";
import type { AOSConfig } from "./types";

let _guardStyle: HTMLStyleElement | null = null;
let _initialized = false;

async function init(): Promise<void> {
  if (_initialized) return;

  let config: AOSConfig;

  try {
    config = readConfig();
  } catch (e) {
    console.error("[AOS]", e);
    return; // No config = can't do anything, default content stays visible
  }

  // Step 1: Inject CSS Guard immediately (before any async work)
  _guardStyle = injectGuard(config.customSelectors);

  try {
    // Step 2: Perform handshake with the API
    const payload = await performHandshake(config);

    // Step 3: Initialize tracker with session context
    initTracker(
      config.apiUrl,
      config.publicKey,
      payload.session_id,
      payload.variation_id
    );

    // Step 4: Swap content into slots
    const applied = renderSlots(payload.slots);

    // Step 5: Reveal slots (fade in)
    revealSlots(_guardStyle);

    // Step 6: Fire impression event
    if (applied > 0) {
      track("impression", {
        vibe: payload.vibe,
        is_control: payload.is_control,
        slots_applied: applied,
      });
    }

    // Step 7: Set up auto-tracking
    autoTrackForms();
    autoTrackClicks();

    _initialized = true;
  } catch (error) {
    console.warn("[AOS] SDK error, falling back to default content:", error);
    removeGuard(_guardStyle);
  }
}

// Execute immediately when script loads
init();

// Expose public API
export { track, init };
