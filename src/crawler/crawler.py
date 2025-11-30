import asyncio
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from src.database.db import init_db
from src.utils.tag_parsers import parse_category, parse_ratings
from src.utils.urls import base_url, get_full_url


async def fetch_html(session: aiohttp.ClientSession, url: str, semaphore):
    """Fetch HTML content from URL"""
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


async def fetch_category_links(session: aiohttp.ClientSession, semaphore) -> List[str]:
    """Fetch all category links"""
    html = await fetch_html(session, base_url, semaphore)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links = []

    for link in soup.select("div.side_categories a"):
        href = link.get("href")
        if href:
            full_url = urljoin(base_url, href)
            links.append(full_url)

    return links[1:]


async def fetch_book_links(
    session: aiohttp.ClientSession, url: str, semaphore
) -> List[str]:
    """Fetch all book links from a page"""
    html = await fetch_html(session, url, semaphore)
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
    session: aiohttp.ClientSession, current_url: str, semaphore
) -> Optional[str]:
    """Fetch next page URL if it exists"""
    html = await fetch_html(session, current_url, semaphore)
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
    session: aiohttp.ClientSession, url: str, semaphore
) -> Optional[dict]:
    """Fetch and parse book details"""
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

            title = book.find("h1").text
            cover = get_full_url(book.find("img")["src"])
            category = parse_category(book)
            ratings = parse_ratings(book)
            description = book.find("meta", attrs={"name": "description"}).get(
                "content"
            )

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
    session: aiohttp.ClientSession, page_url: str, semaphore, save_to_db_func=None
) -> tuple[List[dict], Optional[str]]:
    """Scrape all books from a page and optionally save to DB"""
    book_links = await fetch_book_links(session, page_url, semaphore)

    book_tasks = [fetch_book_details(session, link, semaphore) for link in book_links]
    books = await asyncio.gather(*book_tasks)

    books = [book for book in books if book is not None]

    # Save to database if function provided
    if save_to_db_func and books:
        result = save_to_db_func(books)
        print(f"✓ Saved {result['inserted']} new, updated {result['updated']} books")

    next_url = await fetch_next_page_url(session, page_url, semaphore)

    return books, next_url


async def scrape_category(
    session: aiohttp.ClientSession, category_url: str, semaphore, save_to_db_func=None
) -> List[dict]:
    """Scrape all books from a category (handles pagination)"""
    all_books = []
    current_url = category_url
    page_num = 1

    while current_url is not None:
        print(f"Scraping category page {page_num}: {current_url}")
        books, current_url = await scrape_page_books(
            session, current_url, semaphore, save_to_db_func
        )
        all_books.extend(books)
        page_num += 1

    return all_books


async def scrape_website(save_to_db: bool = True) -> dict:
    """
    Main logic of the crawler

    Args:
        save_to_db: If True, saves books to MongoDB as they're scraped

    Returns:
        Dictionary with scraping statistics
    """
    semaphore = asyncio.Semaphore(10)
    all_books = []

    save_func = None
    if save_to_db:
        from src.database.db import save_books_batch

        init_db()
        save_func = save_books_batch

    start_time = datetime.now()

    async with aiohttp.ClientSession() as session:
        categories = await fetch_category_links(session, semaphore)
        print(f"Found {len(categories)} categories")

        category_tasks = [
            scrape_category(session, category, semaphore, save_func)
            for category in categories
        ]
        results = await asyncio.gather(*category_tasks)

        for category_books in results:
            all_books.extend(category_books)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    return {
        "status": "success",
        "total_books": len(all_books),
        "duration_seconds": duration,
        "scraped_at": end_time.isoformat(),
        "saved_to_db": save_to_db,
    }


def run_scraper(save_to_db: bool = True) -> dict:
    """Entry point of the website crawling algorithm"""
    return asyncio.run(scrape_website(save_to_db))
