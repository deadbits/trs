import os
import sys
import time
import redis
import feedparser

from loguru import logger

from pydantic import BaseModel
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler

from trs.main import TRS


feed_list = {
    'http://example.com/rss1': 10,  # every 10 minutes
    'http://example.com/rss2': 30,  # every 30 minutes
}


class FeedItem(BaseModel):
    title: str
    link: str
    summary: str


class RedisDB:
    def __init__(self):
        self.rdb = redis.Redis(
            host='localhost',
            port=6379,
            db=0
        )

    def set_item(self, key: str, value: str) -> None:
        try:
            self.rdb.set(key, value)
        except redis.RedisError as e:
            logging.error(f"Error setting key-value in Redis: {e}")

    def get_item(self, key: str) -> Optional[bytes]:
        try:
            return self.rdb.get(key)
        except redis.RedisError as e:
            logging.error(f"Error getting key-value in Redis: {e}")
            return None


def fetch_feed(url: str) -> None:
    try:
        d = feedparser.parse(url)
        for entry in d.entries:
            item = FeedItem(title=entry.title, link=entry.link, summary=entry.summary)
            rdb.set_item(item.link, item.json())
            doc = trs.url_to_doc(item.link)
    except Exception as e:
        logging.error(f"Error fetching feed: {e}")


if __name__ == '__main__':
    OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
    if OPENAI_KEY is None:
        logger.error('OPENAI_API_KEY environment variable not set')
        sys.exit(1)

    trs = TRS(openai_key=OPENAI_KEY)

    rdb = RedisDB()

    scheduler = BackgroundScheduler()

    for url, minutes in feed_list.items():
        scheduler.add_job(fetch_feed, 'interval', [url, rdb], minutes=minutes)

    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
