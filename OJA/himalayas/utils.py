"""Shared helpers for Himalayas API scripts."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values
from OJA.db_handler import OJADBHandler

API_URL   = "https://himalayas.app/jobs/api"
PAGE_SIZE = 20
SLEEP_SEC = 0.5

log = logging.getLogger(__name__)


def load_db_config(env_path: Path = None) -> dict:
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"
    config = dotenv_values(env_path)
    return {
        "host": config["DB_HOST"],
        "database": config["DB_DATABASE"],
        "user": config["DB_USER"],
        "password": config["DB_PASSWORD"],
        "port": config.get("DB_PORT", 5432),
    }


def ts_to_dt(unix_ts):
    if unix_ts is None:
        return None
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc)


def fetch_page(session: requests.Session, offset: int) -> dict:
    resp = session.get(
        API_URL,
        params={"offset": offset, "limit": PAGE_SIZE},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def insert_job(db: OJADBHandler, job: dict) -> bool:
    """Insert a job and all its related rows. Returns True if inserted, False if skipped."""
    source_url = job.get("guid")
    if not source_url:
        log.warning("Job has no guid, skipping: %s", job.get("title"))
        return False

    company_id = db.get_or_create_company(name=job.get("companyName"), website_url=None)

    job_id = db.insert_job_posting(
        source_url=source_url,
        source_id=source_url,
        source_name="himalayas.app",
        title=job.get("title"),
        description_html=job.get("description"),
        description_text=job.get("description"),
        meta_description=None,
        employment_type=job.get("employmentType"),
        location=None,
        date_posted=ts_to_dt(job.get("pubDate")),
        company_id=company_id,
        min_salary=job.get("minSalary"),
        max_salary=job.get("maxSalary"),
        currency=job.get("currency"),
        date_expires=ts_to_dt(job.get("expiryDate")),
    )

    if job_id is None:
        return False

    for s in (job.get("seniority") or []):
        db.attach_seniority(job_id, db.get_or_create_seniority(s))
    for c in (job.get("categories") or []):
        db.attach_category(job_id, db.get_or_create_category(c))
    for pc in (job.get("parentCategories") or []):
        db.attach_parent_category(job_id, db.get_or_create_parent_category(pc))
    for loc in (job.get("locationRestrictions") or []):
        db.attach_location_restriction(job_id, db.get_or_create_location_restriction(loc))
    for tz in (job.get("timezoneRestrictions") or []):
        db.attach_timezone_restriction(job_id, db.get_or_create_timezone_restriction(float(tz)))

    db.conn.commit()
    return True
