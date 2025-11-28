#!/usr/bin/env python3


import requests
from bs4 import BeautifulSoup


def parse_ratings(book: BeautifulSoup):
    ratings = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    p = book.find(
        "p",
        class_=lambda x: x and any(rating in x for rating in ratings.keys()),  # pyright: ignore[reportArgumentType]
    )

    if p:
        for rating_word, rating_num in ratings.items():
            if rating_word in p.get("class"):
                return rating_num

    return None  # Return None if no rating found


def parse_book_id_html(book: BeautifulSoup):
    url = f"https://books.toscrape.com/catalogue/{book}/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    return soup


def parse_category(book: BeautifulSoup):
    breadcrumbs = book.find("ul", class_="breadcrumb").find_all("li")
    category = breadcrumbs[-2].find("a").text

    return category
