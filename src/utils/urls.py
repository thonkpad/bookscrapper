from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

base_url = "https://books.toscrape.com/"


def get_full_url(url):
    return urljoin(base_url, url)


def get_full_html(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    return soup


def get_category_links():
    soup = get_full_html(base_url)

    links = []
    for link in soup.select("div.side_categories a"):
        href = link.get("href")
        if href:
            full_url = get_full_url(href)
            links.append(full_url)

    return links[1:]  # exclude the index category which shows all books


def get_book_links(url):
    soup = get_full_html(url)

    links = []
    for link in soup.select("article.product_pod"):
        title_link = link.select_one("h3 a")
        if title_link:
            href = title_link.get("href")
            full_url = get_full_url(href)
            links.append(full_url)
    return links
