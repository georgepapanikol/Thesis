"""
initial_population.py
---------------------
Fetches ALL job postings from the Himalayas API (paginating until exhausted)
and inserts them into the PostgreSQL database.
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

    offset, total_fetched, total_inserted = 0, 0, 0
    log.info("Starting initial population...")

    while True:
        log.info("Fetching offset=%d...", offset)
        data = fetch_page(session, offset)
        jobs = data.get("jobs", [])

        if not jobs:
            log.info("No more jobs returned. Done.")
            break

        for job in jobs:
            if insert_job(db, job):
                total_inserted += 1

        total_fetched += len(jobs)
        log.info("  page done: fetched=%d  inserted_this_run=%d", total_fetched, total_inserted)

        total_count = data.get("totalCount", 0)
        offset += PAGE_SIZE
        if offset >= total_count:
            log.info("Reached totalCount=%d. Done.", total_count)
            break

        time.sleep(SLEEP_SEC)

    db.disconnect()
    log.info("Finished. Total inserted: %d", total_inserted)


if __name__ == "__main__":
    run()
