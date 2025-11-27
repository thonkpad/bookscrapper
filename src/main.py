from fastapi import FastAPI
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

app = FastAPI()


@app.get("/books")
async def get_books(
    category: str = "all",
    min_price: float = 0.0,
    max_price: float = 999.999,
    rating: int = 5,
    sort_by: str = "none",
):
    return {"todo": "books"}


@app.get("/books/{book_id}")
async def get_book_id(book_id: str):
    url = f"https://books.toscrape.com/catalogue/{book_id}/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    title = soup.find(
        "h1"
    ).text  # pyright: ignore[reportAny, reportOptionalMemberAccess]

    cover = urljoin(
        "https://books.toscrape.com", soup.find("img")["src"]
    )  # pyright: ignore[reportOptionalSubscript]

    description = soup.find("meta", attrs={"name": "description"}).get("content")

    table = soup.find("table")
    information = {}

    for row in table.find_all("tr"):  # pyright: ignore[reportOptionalMemberAccess]
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
        "description": description,
        "information": information,
    }


@app.get("/changes")
async def get_changes():
    return {"todo": "changes"}


@app.get("/")
async def read_root():
    return {"hello": "world"}
