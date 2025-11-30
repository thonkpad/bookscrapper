from src.utils.tag_parsers import parse_book_id_html, parse_category, parse_ratings
from src.utils.urls import get_full_html, get_full_url


def get_book_details(book_id: str) -> dict:
    book = parse_book_id_html(book_id)

    title = book.find("h1").text
    cover = get_full_url(book.find("img")["src"])
    category = parse_category(book)
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


def get_book_html_details(url: str) -> dict:
    book = get_full_html(url)

    title = book.find("h1").text
    cover = get_full_url(book.find("img")["src"])
    category = parse_category(book)
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
