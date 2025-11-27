#!/usr/bin/env python3


from bs4 import BeautifulSoup
import requests


def parse_ratings(soup: BeautifulSoup):
    ratings = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    p = soup.find(
        "p", class_=lambda x: x and any(rating in x for rating in ratings.keys())
    )

    if p:
        for rating_word, rating_num in ratings.items():
            if rating_word in p.get("class"):
                return rating_num
    
    return None  # Return None if no rating found

def parse_book_id_html(book_id):
    url = f"https://books.toscrape.com/catalogue/{book_id}/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    return soup
