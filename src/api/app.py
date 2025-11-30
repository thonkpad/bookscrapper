from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.rate_limit import limiter
from src.api.routes import books, changes
from src.database.db import lifespan

app = FastAPI(
    title="Book Scraper API",
    description="API for scraping and managing book data with change tracking",
    version="1.0.0",
    lifespan=lifespan,
)

# Include rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(changes.router, prefix="/changes", tags=["Changes"])


@app.get("/")
async def root():
    return {
        "message": "Book Scraper API",
        "version": "1.0.0",
        "endpoints": {"books": "/books", "changes": "/changes", "docs": "/docs"},
    }


@app.get("/health")
@limiter.limit("100/hour")
async def health_check(request: Request):
    return {"status": "healthy"}
