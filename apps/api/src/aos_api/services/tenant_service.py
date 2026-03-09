"""
Tenant service: validates public keys and origins.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aos_api.db.models import Tenant


async def get_tenant_by_public_key(db: AsyncSession, public_key: str) -> Tenant | None:
    """Fetch tenant by public key."""
    result = await db.execute(select(Tenant).where(Tenant.public_key == public_key))
    return result.scalar_one_or_none()


def validate_origin(tenant: Tenant, origin: str | None, environment: str = "development") -> bool:
    """Check if the request origin is allowed for this tenant."""
    if environment == "development":
        # In dev, allow all localhost origins
        if not origin:
            return True
        return (
            origin.startswith("http://localhost")
            or origin.startswith("http://127.0.0.1")
            or origin.startswith("file://")
        )

    if not origin:
        return False

    return origin in (tenant.allowed_origins or [])
