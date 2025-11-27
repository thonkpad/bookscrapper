from fastapi import APIRouter
from api.services.books_service import get_book_details

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
async def get_books(
    category: str = "all",
    min_price: float = 0.0,
    max_price: float = 99.99,
    rating: int = 5,
    sort_by: str = "none",
):
    return {"todo": "books"}


@router.get("/{book_id}")
async def get_book_id(book_id: str):
    return get_book_details(book_id)
