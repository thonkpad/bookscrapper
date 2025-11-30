from fastapi import FastAPI

from src.api.routes import books, changes
from src.database.db import lifespan

app = FastAPI(
    title="Book Scraper API",
    description="API for scraping and managing book data with change tracking",
    version="1.0.0",
    lifespan=lifespan,
)

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
async def health_check():
    return {"status": "healthy"}
