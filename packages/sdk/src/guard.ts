/**
 * Critical CSS Guard: hides AOS-targeted elements immediately
 * to prevent FOUC (Flash of Unstyled Content).
 * Removed after variation content is swapped in.
 */

export function injectGuard(customSelectors: string): HTMLStyleElement {
  const style = document.createElement("style");
  style.id = "aos-critical-guard";

  // Always hide data-aos-slot elements
  let css =
    "[data-aos-slot] { opacity: 0 !important; transition: opacity 0.3s ease; }\n";

  // Also hide merchant-configured CSS selectors
  if (customSelectors) {
    const selectors = customSelectors
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (selectors.length > 0) {
      css += `${selectors.join(", ")} { opacity: 0 !important; transition: opacity 0.3s ease; }\n`;
    }
  }

  style.textContent = css;

  // Inject at the very top of <head> for maximum priority
  const head = document.head || document.documentElement;
  head.insertBefore(style, head.firstChild);

  return style;
}

export function revealSlots(guardStyle: HTMLStyleElement): void {
  // Flip opacity to 1 for all guarded elements
  guardStyle.textContent =
    "[data-aos-slot] { opacity: 1 !important; transition: opacity 0.3s ease; }";

  // Clean up the style tag after transition completes
  setTimeout(() => {
    guardStyle.remove();
  }, 400);
}

export function removeGuard(guardStyle: HTMLStyleElement | null): void {
  if (!guardStyle) return;
  // On error: immediately reveal default content
  guardStyle.textContent =
    "[data-aos-slot] { opacity: 1 !important; }";
  setTimeout(() => guardStyle.remove(), 400);
}
