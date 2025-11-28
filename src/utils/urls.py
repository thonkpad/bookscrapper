from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

base_url = "https://books.toscrape.com/"


def get_full_url(url):
    return urljoin(base_url, url)


def get_category_links():
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, "lxml")

    links = []
    for link in soup.select("div.side_categories a"):
        href = link.get("href")
        if href:
            full_url = get_full_url(href)
            links.append(full_url)

    return links[1:]  # exclude the index category which shows all books
