"""
initial_population.py

Performs the first-time population of the database from kariera.gr.
Scrapes ALL available pages until an empty page is encountered, then stops.

Usage:
    python initial_population.py
    python initial_population.py --limit 100
"""

import time
import re
import argparse
import requests
from dotenv import dotenv_values
from urllib.parse import urljoin
from OJA.kariera.scraper import _fetch, _strip_query, process_url, BASE_URL, LIST_URL, REQUEST_DELAY
from OJA.db_handler import OJADBHandler
from pathlib import Path


def _get_urls_from_page(page: int, limit: int, session: requests.Session) -> list[str]:
    """Return job URLs found on a single list page."""
    url = f"{LIST_URL}?page={page}&limit={limit}&cps=48"
    soup = _fetch(url, session)
    if soup is None:
        return []

    urls = []
    for a in soup.find_all("a", class_=re.compile(r"BaseJobCard_jobTitle")):
        href = a.get("href", "")
        if "/en/jobs/" in href:
            urls.append(urljoin(BASE_URL, _strip_query(href)))
    return urls


def run(limit: int = 100):
    config = dotenv_values(Path(__file__).parent.parent / ".env")
    db_config = {
        "host": config["DB_HOST"],
        "database": config["DB_DATABASE"],
        "user": config["DB_USER"],
        "password": config["DB_PASSWORD"],
        "port": config.get("DB_PORT", 5432),
    }

    session = requests.Session()
    inserted = skipped = failed = total = 0
    page = 0

    print("Starting initial population...\n")

    with OJADBHandler(db_config) as db:
        while True:
            print(f"── Page {page} ──────────────────────────────")
            urls = _get_urls_from_page(page, limit, session)
            time.sleep(REQUEST_DELAY)

            if not urls:
                print("  Empty page — reached end of listings.")
                break

            for i, url in enumerate(urls, start=1):
                total += 1
                print(f"  [{i}/{len(urls)}] {url}")
                result = process_url(url, session, db)
                if result == "inserted":
                    inserted += 1
                    print("    ✓ inserted")
                elif result == "skipped":
                    skipped += 1
                    print("    → already in DB")
                else:
                    failed += 1
                    print("    ✗ failed")
                time.sleep(REQUEST_DELAY)

            page += 1

    print("\n" + "=" * 50)
    print(f"  Pages processed : {page}")
    print(f"  Inserted        : {inserted}")
    print(f"  Skipped         : {skipped}")
    print(f"  Failed          : {failed}")
    print(f"  Total           : {total}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initial DB population from kariera.gr")
    parser.add_argument("--limit", type=int, default=100, help="Jobs per page (max 100)")
    args = parser.parse_args()
    run(limit=args.limit)
