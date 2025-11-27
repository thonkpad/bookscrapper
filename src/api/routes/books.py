from fastapi import APIRouter
import utils.helpers as helpers
from urllib.parse import urljoin

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
async def get_books(
    category: str = "all",
    min_price: float = 0.0,
    max_price: float = 999.999,
    rating: int = 5,
    sort_by: str = "none",
):
    return {"todo": "books"}


@router.get("/{book_id}")
async def get_book_id(book_id: str):
    book = helpers.parse_book_id_html(book_id)

    title = book.find("h1").text

    cover = urljoin("https://books.toscrape.com", book.find("img")["src"])

    category = "todo"

    ratings = helpers.parse_ratings(book)

    description = book.find("meta", attrs={"name": "description"}).get("content")

    table = book.find("table")
    information = {}

    for row in table.find_all("tr"):
        columns = row.find_all(["th", "td"])
        if len(columns) == 2:
            key = columns[0].text.strip()
            value = columns[1].text.strip()

            if "Price" in key or key == "Tax":
                value = value.replace("Â£", "£")
            information[key] = value

    return {
        "title": title,
        "cover": cover,
        "category": category,
        "ratings": ratings,
        "description": description,
        "information": information,
    }
