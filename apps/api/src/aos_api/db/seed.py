"""
Seed script: Creates demo tenant with hero slot and 4 variations (1 control + 3 vibes).
Run with: python -m aos_api.db.seed
"""
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.models import Tenant, Slot, Variation, MabState
from aos_api.db.session import async_session_factory, engine


DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
HERO_HEADLINE_SLOT_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
HERO_SUBHEADLINE_SLOT_ID = uuid.UUID("00000000-0000-0000-0000-000000000011")
HERO_CTA_SLOT_ID = uuid.UUID("00000000-0000-0000-0000-000000000012")
HERO_IMAGE_SLOT_ID = uuid.UUID("00000000-0000-0000-0000-000000000013")


async def seed(session: AsyncSession):
    # Check if demo tenant already exists
    result = await session.execute(
        select(Tenant).where(Tenant.public_key == "pk_demo_001")
    )
    if result.scalar_one_or_none():
        print("Demo tenant already exists, skipping seed.")
        return

    # --- Tenant ---
    tenant = Tenant(
        id=DEMO_TENANT_ID,
        name="Aura Wellness (Demo)",
        public_key="pk_demo_001",
        secret_key="sk_demo_001",
        allowed_origins=[
            "http://localhost:3000",
            "http://localhost:5500",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5500",
        ],
    )
    session.add(tenant)

    # --- Slots ---
    slots = [
        Slot(
            id=HERO_HEADLINE_SLOT_ID,
            tenant_id=DEMO_TENANT_ID,
            slot_key="hero-headline",
            selector='[data-aos-slot="hero-headline"]',
        ),
        Slot(
            id=HERO_SUBHEADLINE_SLOT_ID,
            tenant_id=DEMO_TENANT_ID,
            slot_key="hero-subheadline",
            selector='[data-aos-slot="hero-subheadline"]',
        ),
        Slot(
            id=HERO_CTA_SLOT_ID,
            tenant_id=DEMO_TENANT_ID,
            slot_key="hero-cta",
            selector='[data-aos-slot="hero-cta"]',
        ),
        Slot(
            id=HERO_IMAGE_SLOT_ID,
            tenant_id=DEMO_TENANT_ID,
            slot_key="hero-image",
            selector='[data-aos-slot="hero-image"]',
        ),
    ]
    session.add_all(slots)

    # --- Variations ---
    # Each "variation set" has entries for all 4 slots sharing a vibe_segment.
    # The variation_id used for attribution is a group ID (one per vibe).

    variations_data = [
        # Control (default)
        {
            "vibe": "default",
            "name_prefix": "Control",
            "is_control": True,
            "content": {
                "hero-headline": {
                    "action": "replace_text",
                    "value": "Wellness That Fits Your Life",
                },
                "hero-subheadline": {
                    "action": "replace_text",
                    "value": "Science-backed supplements designed for real results. Join 50,000+ customers who transformed their routine.",
                },
                "hero-cta": {
                    "action": "replace_text",
                    "value": "Shop Now",
                },
                "hero-image": {
                    "action": "replace_src",
                    "value": "https://placehold.co/600x400/e2e8f0/475569?text=Aura+Wellness",
                },
            },
        },
        # Casual / TikTok
        {
            "vibe": "casual",
            "name_prefix": "TikTok Glow-Up",
            "is_control": False,
            "content": {
                "hero-headline": {
                    "action": "replace_text",
                    "value": "Your Glow-Up Starts Here",
                },
                "hero-subheadline": {
                    "action": "replace_text",
                    "value": "Trending for a reason. 500K+ TikTok fans can't be wrong.",
                },
                "hero-cta": {
                    "action": "replace_text",
                    "value": "Get the Glow",
                },
                "hero-image": {
                    "action": "replace_src",
                    "value": "https://placehold.co/600x400/fef3c7/92400e?text=Glow+Up",
                },
            },
        },
        # Minimalist / Pinterest
        {
            "vibe": "minimalist",
            "name_prefix": "Pinterest Minimal",
            "is_control": False,
            "content": {
                "hero-headline": {
                    "action": "replace_text",
                    "value": "Elevate Your Daily Ritual",
                },
                "hero-subheadline": {
                    "action": "replace_text",
                    "value": "Thoughtfully formulated. Minimally designed. Maximum results.",
                },
                "hero-cta": {
                    "action": "replace_text",
                    "value": "Discover the Collection",
                },
                "hero-image": {
                    "action": "replace_src",
                    "value": "https://placehold.co/600x400/f0fdf4/14532d?text=Daily+Ritual",
                },
            },
        },
        # Bold / Instagram
        {
            "vibe": "bold",
            "name_prefix": "Bold Aesthetic",
            "is_control": False,
            "content": {
                "hero-headline": {
                    "action": "replace_text",
                    "value": "OWN YOUR EDGE",
                },
                "hero-subheadline": {
                    "action": "replace_text",
                    "value": "Bold formulas for bold people. Stand out from the crowd.",
                },
                "hero-cta": {
                    "action": "replace_text",
                    "value": "Claim Yours",
                },
                "hero-image": {
                    "action": "replace_src",
                    "value": "https://placehold.co/600x400/fecaca/991b1b?text=OWN+YOUR+EDGE",
                },
            },
        },
    ]

    slot_id_map = {
        "hero-headline": HERO_HEADLINE_SLOT_ID,
        "hero-subheadline": HERO_SUBHEADLINE_SLOT_ID,
        "hero-cta": HERO_CTA_SLOT_ID,
        "hero-image": HERO_IMAGE_SLOT_ID,
    }

    for var_data in variations_data:
        for slot_key, content in var_data["content"].items():
            variation = Variation(
                id=uuid.uuid4(),
                slot_id=slot_id_map[slot_key],
                name=f"{var_data['name_prefix']} — {slot_key}",
                vibe_segment=var_data["vibe"],
                content_json=content,
                is_control=var_data["is_control"],
            )
            session.add(variation)
            await session.flush()

            # Initialize MAB state for each variation
            mab = MabState(
                id=uuid.uuid4(),
                variation_id=variation.id,
                alpha=1.0,
                beta=1.0,
            )
            session.add(mab)

    await session.commit()
    print("Demo tenant seeded successfully!")
    print(f"  Public Key: pk_demo_001")
    print(f"  Secret Key: sk_demo_001")
    print(f"  Slots: hero-headline, hero-subheadline, hero-cta, hero-image")
    print(f"  Vibes: default (control), casual, minimalist, bold")


async def main():
    async with async_session_factory() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
