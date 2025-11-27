from urllib.parse import urljoin
from utils.helpers import parse_book_id_html, parse_ratings


def get_book_details(book_id: str) -> dict:
    book = parse_book_id_html(book_id)

    title = book.find("h1").text
    cover = urljoin("https://books.toscrape.com", book.find("img")["src"])
    category = "todo"
    ratings = parse_ratings(book)
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
