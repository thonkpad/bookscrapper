from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from api.auth import get_api_key
from api.rate_limit import limiter
from src.database.db import get_recent_changes

router = APIRouter()


@router.get("/")
@limiter.limit("100/hour")
async def list_changes(
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Number of changes to return"),
    change_type: Optional[str] = Query(
        None, regex="^(new_book|price_change)$", description="Filter by change type"
    ),
    api_key: str = Depends(get_api_key),
):
    """
    Get recent changes (new books added, price changes, etc.)

    - **limit**: Maximum number of changes to return
    - **change_type**: Filter by 'new_book' or 'price_change'
    """
    changes = get_recent_changes(limit=limit, change_type=change_type)

    return {"count": len(changes), "changes": changes}
