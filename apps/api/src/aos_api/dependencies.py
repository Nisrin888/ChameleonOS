"""
FastAPI dependencies: database session, Redis client, tenant validation.
"""
from fastapi import Depends, Header, HTTPException

from aos_api.db.models import Tenant
from aos_api.db.session import get_db
from aos_api.redis_client import get_redis
from aos_api.services.tenant_service import get_tenant_by_public_key


async def get_tenant_from_key(
    public_key: str,
    db=Depends(get_db),
) -> Tenant:
    """Resolve a tenant from public_key (provided in request body)."""
    tenant = await get_tenant_by_public_key(db, public_key)
    if not tenant:
        raise HTTPException(status_code=404, detail="Invalid public key")
    return tenant
