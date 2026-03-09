import type { SlotPayload } from "./types";

/**
 * For each slot in the variation payload, find the target element
 * and swap its content based on the action type.
 */
export function renderSlots(slots: SlotPayload[]): number {
  let applied = 0;

  for (const slot of slots) {
    const el = resolveElement(slot.slot_id, slot.selector);
    if (!el) {
      console.warn(`[AOS] Slot target not found: ${slot.selector}`);
      continue;
    }

    switch (slot.action) {
      case "replace_text":
        el.textContent = slot.value;
        break;
      case "replace_html":
        el.innerHTML = slot.value;
        break;
      case "replace_src":
        if ("src" in el) {
          (el as HTMLImageElement).src = slot.value;
        }
        break;
      case "replace_bg":
        (el as HTMLElement).style.backgroundImage = `url('${slot.value}')`;
        break;
    }

    applied++;
  }

  return applied;
}

/**
 * Resolve a DOM element by slot_id (data attribute) or CSS selector.
 * Priority: data-aos-slot attribute > CSS selector.
 */
function resolveElement(
  slotId: string,
  selector: string
): Element | null {
  // First: try data-aos-slot attribute match
  const slotEl = document.querySelector(`[data-aos-slot="${slotId}"]`);
  if (slotEl) return slotEl;

  // Second: try CSS selector
  try {
    return document.querySelector(selector);
  } catch {
    console.warn(`[AOS] Invalid selector: ${selector}`);
    return null;
  }
}
