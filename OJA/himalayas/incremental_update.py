"""
incremental_update.py
---------------------
Fetches new job postings from the Himalayas API and stops as soon as it
encounters a posting whose source_url already exists in the database.

The API returns jobs newest-first, so the first known guid means everything
after it is already stored.
"""

import time
import logging

import requests
from OJA.db_handler import OJADBHandler
from OJA.himalayas.utils import PAGE_SIZE, SLEEP_SEC, fetch_page, insert_job, load_db_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
log = logging.getLogger(__name__)


def run():
    db = OJADBHandler(load_db_config())
    db.connect()
    session = requests.Session()

    offset, total_inserted = 0, 0
    log.info("Starting incremental update ...")

    while True:
        log.info("Fetching offset=%d ...", offset)
        data = fetch_page(session, offset)
        jobs = data.get("jobs", [])

        if not jobs:
            log.info("No jobs returned. Nothing new.")
            break

        stop = False
        for job in jobs:
            url = job.get("guid")
            if url and db.url_exists(url):
                log.info("Found existing entry: %s — stopping here.", url)
                stop = True
                break
            if insert_job(db, job):
                total_inserted += 1

        if stop:
            break

        total_count = data.get("totalCount", 0)
        offset += PAGE_SIZE
        if offset >= total_count:
            log.info("Reached end of feed (totalCount=%d).", total_count)
            break

        time.sleep(SLEEP_SEC)

    db.disconnect()
    log.info("Incremental update finished. New jobs inserted: %d", total_inserted)


if __name__ == "__main__":
    run()
