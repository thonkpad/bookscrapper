from fastapi import APIRouter


router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("/changes")
async def get_changes():
    return {"todo": "changes"}
