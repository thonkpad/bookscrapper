import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

client = None
db = None
books_collection = None
changes_collection = None


def init_db():
    global client, db, books_collection, changes_collection

    if books_collection is not None:
        return  # Already initialized

    uri = os.getenv("MONGO_URL")
    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client["books"]
    books_collection = db["books"]
    changes_collection = db["changes"]

    # Create indexes
    books_collection.create_index("title")
    books_collection.create_index("category")
    books_collection.create_index("ratings")
    books_collection.create_index("scraped_at")
    books_collection.create_index([("title", 1), ("category", 1)], unique=True)

    changes_collection.create_index([("timestamp", DESCENDING)])
    changes_collection.create_index("book_id")
    changes_collection.create_index("change_type")

    print("✓ MongoDB initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for MongoDB connection"""
    global client, db, books_collection, changes_collection

    uri = os.getenv("MONGO_URL")

    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client["books"]
    books_collection = db["books"]
    changes_collection = db["changes"]

    books_collection.create_index("title")
    books_collection.create_index("category")
    books_collection.create_index("ratings")
    books_collection.create_index("scraped_at")
    books_collection.create_index([("title", 1), ("category", 1)], unique=True)

    changes_collection.create_index([("timestamp", DESCENDING)])
    changes_collection.create_index("book_id")
    changes_collection.create_index("change_type")

    print("✓ Connected to MongoDB")

    try:
        client.admin.command("ping")
        print("✓ MongoDB connection verified")
        yield
    finally:
        if client:
            client.close()
            print("✗ MongoDB connection closed")


def get_collection():
    """Get the books collection"""
    return books_collection


def extract_price(price_str: str) -> float:
    """Extract numeric price from string like '£19.99'"""
    try:
        return float(price_str.replace("£", "").replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def save_book_to_db(book_data: dict) -> dict:
    """Save a single book to MongoDB (upsert to avoid duplicates)"""
    book_data["scraped_at"] = datetime.now()

    # Extract price for easier querying
    if "information" in book_data and "Price (excl. tax)" in book_data["information"]:
        book_data["price"] = extract_price(
            book_data["information"]["Price (excl. tax)"]
        )

    # Check if book exists for change tracking
    existing_book = books_collection.find_one(
        {"title": book_data["title"], "category": book_data["category"]}
    )

    result = books_collection.update_one(
        {"title": book_data["title"], "category": book_data["category"]},
        {"$set": book_data},
        upsert=True,
    )

    # Track changes
    if existing_book:
        # Check for price change
        old_price = existing_book.get("price", 0)
        new_price = book_data.get("price", 0)
        if old_price != new_price:
            log_change(
                book_id=str(existing_book["_id"]),
                change_type="price_change",
                old_value=old_price,
                new_value=new_price,
                book_title=book_data["title"],
            )
    else:
        # New book added
        if result.upserted_id:
            log_change(
                book_id=str(result.upserted_id),
                change_type="new_book",
                old_value=None,
                new_value=None,
                book_title=book_data["title"],
            )

    return {
        "matched": result.matched_count,
        "modified": result.modified_count,
        "upserted_id": str(result.upserted_id) if result.upserted_id else None,
    }


def save_books_batch(books: list[dict]) -> dict:
    """Save multiple books to MongoDB in a batch operation"""
    if not books:
        return {"inserted": 0, "updated": 0, "errors": 0}

    inserted = 0
    updated = 0
    errors = 0

    for book in books:
        try:
            result = save_book_to_db(book)
            if result["upserted_id"]:
                inserted += 1
            elif result["modified"] > 0:
                updated += 1
        except Exception as e:
            print(f"Error saving book {book.get('title', 'Unknown')}: {e}")
            errors += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "errors": errors,
        "total": len(books),
    }


def get_books(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rating: Optional[int] = None,
    sort_by: str = "title",
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Get books with filtering, sorting, and pagination
    """
    query = {}
    if category:
        query["category"] = category
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if rating is not None:
        query["ratings"] = rating

    sort_field = sort_by
    sort_order = ASCENDING

    sort_mapping = {
        "rating": ("ratings", DESCENDING),
        "price": ("price", ASCENDING),
        "reviews": ("information.Number of reviews", DESCENDING),
        "title": ("title", ASCENDING),
    }

    if sort_by in sort_mapping:
        sort_field, sort_order = sort_mapping[sort_by]

    skip = (page - 1) * page_size

    total_count = books_collection.count_documents(query)

    cursor = (
        books_collection.find(query)
        .sort(sort_field, sort_order)
        .skip(skip)
        .limit(page_size)
    )
    books = list(cursor)

    for book in books:
        book["_id"] = str(book["_id"])

    total_pages = (total_count + page_size - 1) // page_size

    return {
        "books": books,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def get_book_by_id(book_id: str) -> Optional[dict]:
    """Get a single book by MongoDB ID"""
    try:
        book = books_collection.find_one({"_id": ObjectId(book_id)})
        if book:
            book["_id"] = str(book["_id"])
        return book
    except Exception as e:
        print(f"Error fetching book {book_id}: {e}")
        return None


def get_book_count():
    """Get total count of books in database"""
    return books_collection.count_documents({})


def log_change(
    book_id: str, change_type: str, old_value: Any, new_value: Any, book_title: str
):
    """Log a change to the changes collection"""
    change_doc = {
        "book_id": book_id,
        "book_title": book_title,
        "change_type": change_type,
        "old_value": old_value,
        "new_value": new_value,
        "timestamp": datetime.now(),
    }
    changes_collection.insert_one(change_doc)


def get_recent_changes(limit: int = 50, change_type: Optional[str] = None) -> list:
    """Get recent changes from the database"""
    query = {}
    if change_type:
        query["change_type"] = change_type

    changes = list(
        changes_collection.find(query).sort("timestamp", DESCENDING).limit(limit)
    )

    for change in changes:
        change["_id"] = str(change["_id"])

    return changes
