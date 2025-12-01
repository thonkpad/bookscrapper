import os
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "book_scraper", broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL")
)

app.conf.update(
    task_serilizer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Manila",
    enable_utc=False,
)

app.conf.beat_schedule = {
    "scrape-books-daily-12pm": {
        "task": "src.scheduler.scheduler.scrape_books_task",
        "schedule": crontab(hour=12, minute=30),  # Run at 12:30 PM every day
    },
}


@app.task(bind=True, name="src.scheduler.scheduler.scrape_books_task")
def scrape_books_task(self):
    """
    Celery task to scrape books and save to MongoDB
    """
    try:
        print(f"Starting scrape task at {datetime.now()}")

        from src.crawler.crawler import run_scraper

        result = run_scraper(save_to_db=True)

        print(f"Scrape completed: {result}")

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_books": result.get("total_books", 0),
            "duration_seconds": result.get("duration_seconds", 0),
        }

    except Exception as e:
        print(f"Error in scrape task: {e}")
        # Retry after 5 minutes if failed
        self.retry(exc=e, countdown=300, max_retries=3)
