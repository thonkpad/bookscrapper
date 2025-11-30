from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from api.auth import get_api_key
from src.api.rate_limit import limiter
from src.crawler.crawler import run_scraper
from src.database.db import get_book_by_id, get_book_count, get_books

router = APIRouter()


@router.get("/")
@limiter.limit("100/hour")
async def list_books(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating"),
    sort_by: str = Query(
        "title", regex="^(rating|price|reviews|title)$", description="Sort by field"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(get_api_key),
):
    """
    Get books with filtering, sorting, and pagination

    - **category**: Filter by book category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **rating**: Filter by rating (1-5)
    - **sort_by**: Sort by rating, price, reviews, or title
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    """
    result = get_books(
        category=category,
        min_price=min_price,
        max_price=max_price,
        rating=rating,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )

    return result


@router.get("/{book_id}")
@limiter.limit("100/hour")
async def get_book(
    request: Request,
    book_id: str = Path(..., description="MongoDB ObjectId of the book"),
    api_key: str = Depends(get_api_key),
):
    """
    Get full details about a specific book by ID
    """
    book = get_book_by_id(book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


@router.get("/stats/count")
@limiter.limit("100/hour")
async def count_books(request: Request, api_key: str = Depends(get_api_key)):
    """Get total count of books in database"""
    count = get_book_count()
    return {"count": count}


@router.post("/scrape")
@limiter.limit("100/hour")
async def trigger_scrape(request: Request, api_key: str = Depends(get_api_key)):
    """
    Trigger a full scraping job

    This will scrape all books from the website and save them to the database.
    Changes (new books, price updates) will be tracked automatically.
    """
    result = run_scraper(save_to_db=True)
    return result
