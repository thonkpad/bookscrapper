import asyncio
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup
from requests.compat import urljoin

from src.utils.tag_parsers import parse_category, parse_ratings
from src.utils.urls import (
    base_url,
    get_full_url,
)

# semaphore = asyncio.Semaphore(10)  # concurrent requests


async def fetch_html(session: aiohttp.ClientSession, url: str):
    async with semaphore:
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error: Status {response.status} for {url}")
        except asyncio.TimeoutError:
            print(f"Timeout fetching url: {url}")
        except aiohttp.ClientError as e:
            print(f"Client error fetching {url}: {e}")
    return None


async def fetch_category_links(session: aiohttp.ClientSession) -> List[str]:
    html = await fetch_html(session, base_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links = []

    for link in soup.select("div.side_categories a"):
        href = link.get("href")
        if href:
            full_url = urljoin(base_url, href)
            links.append(full_url)

    return links[1:]  # exclude index category


async def fetch_book_links(session: aiohttp.ClientSession, url: str) -> List[str]:
    html = await fetch_html(session, url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links = []

    for link in soup.select("article.product_pod"):
        title_link = link.select_one("h3 a")
        if title_link:
            href = title_link.get("href")
            full_url = urljoin(url, href)
            links.append(full_url)

    return links


async def fetch_next_page_url(
    session: aiohttp.ClientSession, current_url: str
) -> Optional[str]:
    html = await fetch_html(session, current_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")
    next_li = soup.select_one("li.next")

    if next_li:
        next_link = next_li.select_one("a")
        if next_link:
            href = next_link.get("href")
            return urljoin(current_url, href)

    return None


async def fetch_book_details(
    session: aiohttp.ClientSession, url: str
) -> Optional[dict]:
    try:
        async with semaphore:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    print(f"Error: Status {response.status} for {url}")
                    return None

                content = await response.read()
                book = BeautifulSoup(content, "lxml")

            # Parse all book details
            title = book.find("h1").text
            cover = get_full_url(book.find("img")["src"])
            category = parse_category(book)
            ratings = parse_ratings(book)
            description = book.find("meta", attrs={"name": "description"}).get(
                "content"
            )

            # Parse table information
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

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


async def scrape_page_books(
    session: aiohttp.ClientSession, page_url: str
) -> tuple[List[dict], Optional[str]]:
    book_links = await fetch_book_links(session, page_url)

    book_tasks = [fetch_book_details(session, link) for link in book_links]
    books = await asyncio.gather(*book_tasks)

    books = [book for book in books if book is not None]

    next_url = await fetch_next_page_url(session, page_url)

    return books, next_url


async def scrape_category(
    session: aiohttp.ClientSession, category_url: str
) -> List[dict]:
    all_books = []
    current_url = category_url
    page_num = 1

    while current_url is not None:
        print(f"Scraping category page {page_num}: {current_url}")
        books, current_url = await scrape_page_books(session, current_url)
        all_books.extend(books)
        page_num += 1

    return all_books


async def scrape_website() -> List[dict]:
    """Main logic of the crawler"""
    global semaphore
    semaphore = asyncio.Semaphore(10)

    all_books = []

    async with aiohttp.ClientSession() as session:
        categories = await fetch_category_links(session)
        print(f"Found {len(categories)} categories")

        category_tasks = [scrape_category(session, category) for category in categories]
        results = await asyncio.gather(*category_tasks)

        for category_books in results:
            all_books.extend(category_books)

    return all_books


def run_scraper():
    """Entry point of the website crawling algorithm"""
    return asyncio.run(scrape_website())
