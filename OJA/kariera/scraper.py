"""
Kariera.gr job posting scraper.

Flow:
  1. Fetch list pages (?page=0,1,2,...) and collect job URLs from anchor tags
     with class BaseJobCard_jobTitle__ehsas.
  2. For each job URL, fetch the page and parse:
       - JSON-LD <script type="application/ld+json"> for structured fields
       - <meta name="description"> for meta_description
  3. Upsert company, insert job posting, attach category tag to DB.
"""

import json
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from OJA.db_handler import OJADBHandler

BASE_URL = "https://www.kariera.gr"
LIST_URL = BASE_URL + "/en/jobs"
SOURCE_NAME = "kariera.gr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Seconds to wait between requests to be polite to the server
REQUEST_DELAY = 1.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_query(url: str) -> str:
    """Remove query parameters from a URL (e.g. ?origin=pjp)."""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


def _fetch(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch {url}: {e}")
        return None


def _extract_source_id(path: str) -> Optional[str]:
    """Extract numeric job ID from a path like /en/jobs/tourism-jobs/293691."""
    match = re.search(r"/(\d+)$", path)
    return match.group(1) if match else None


def _extract_category(path: str) -> Optional[str]:
    """Extract category slug from a path like /en/jobs/tourism-jobs/293691."""
    parts = path.rstrip("/").split("/")
    # path parts: ['', 'en', 'jobs', 'tourism-jobs', '293691']
    if len(parts) >= 4:
        return parts[-2]
    return None


def _html_to_text(html: str) -> str:
    """Strip HTML tags and return plain text."""
    return BeautifulSoup(html, "html.parser").get_text(separator="\n").strip()


# ---------------------------------------------------------------------------
# List page: collect job URLs
# ---------------------------------------------------------------------------

def collect_job_urls(pages: int, limit: int, session: requests.Session) -> list[str]:
    """
    Scrape `pages` list pages and return a deduplicated list of job URLs.

    Args:
        pages: Number of pages to scrape (page index starts at 0).
        limit: Number of results per page (kariera.gr supports up to 100).
        session: Requests session to reuse.
    """
    urls = []
    seen = set()

    for page in range(pages):
        list_url = f"{LIST_URL}?page={page}&limit={limit}&cps=48"
        print(f"Fetching list page {page}: {list_url}")
        soup = _fetch(list_url, session)
        if soup is None:
            print(f"  ✗ Skipping page {page}")
            time.sleep(REQUEST_DELAY)
            continue

        anchors = soup.find_all("a", class_=re.compile(r"BaseJobCard_jobTitle"))
        for a in anchors:
            href = a.get("href", "")
            if "/en/jobs/" in href:
                clean = _strip_query(href)
                full_url = urljoin(BASE_URL, clean)
                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)

        print(f"  Found {len(anchors)} cards, total unique so far: {len(urls)}")
        time.sleep(REQUEST_DELAY)

    return urls


# ---------------------------------------------------------------------------
# Job page: parse a single posting
# ---------------------------------------------------------------------------

def parse_job_page(url: str, session: requests.Session) -> Optional[dict]:
    """
    Fetch a job posting page and return a dict ready for DB insertion.
    Returns None if the page could not be fetched or parsed.
    """
    soup = _fetch(url, session)
    if soup is None:
        return None

    # --- JSON-LD ---
    ld_tag = soup.find("script", type="application/ld+json")
    if ld_tag is None:
        print(f"  ✗ No JSON-LD found at {url}")
        return None

    try:
        ld = json.loads(ld_tag.string)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"  ✗ JSON-LD parse error at {url}: {e}")
        return None

    if ld.get("@type") != "JobPosting":
        print(f"  ✗ JSON-LD is not a JobPosting at {url}")
        return None

    # --- meta description ---
    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag["content"] if meta_tag and meta_tag.get("content") else None

    # --- company ---
    org = ld.get("hiringOrganization", {})
    company = {
        "name": org.get("name"),
        "website_url": org.get("sameAs"),
        "logo_url": org.get("logo"),
    }

    # --- description ---
    description_html = ld.get("description")
    description_text = _html_to_text(description_html) if description_html else None

    # --- path-derived fields ---
    path = urlparse(url).path
    source_id = _extract_source_id(path)
    category = _extract_category(path)

    return {
        "source_url": url,
        "source_id": source_id,
        "source_name": SOURCE_NAME,
        "title": ld.get("title", "").strip(),
        "description_html": description_html,
        "description_text": description_text,
        "meta_description": meta_description,
        "employment_type": ld.get("employmentType"),
        "location": ld.get("jobLocation", {}).get("address"),
        "date_posted": ld.get("datePosted"),
        "company": company,
        "category": category,
    }


# ---------------------------------------------------------------------------
# Shared insertion helper
# ---------------------------------------------------------------------------

def process_url(url: str, session: requests.Session, db: OJADBHandler) -> str:
    """
    Fetch, parse and insert a single job posting URL.

    Returns:
        "inserted"  — new row added
        "skipped"   — URL already in DB
        "failed"    — fetch or parse error
    """
    data = parse_job_page(url, session)
    if data is None:
        return "failed"

    company_id = None
    if data["company"].get("name"):
        company_id = db.get_or_create_company(
            name=data["company"]["name"],
            website_url=data["company"].get("website_url"),
        )

    job_id = db.insert_job_posting(
        source_url=data["source_url"],
        source_id=data["source_id"],
        source_name=data["source_name"],
        title=data["title"],
        description_html=data["description_html"],
        description_text=data["description_text"],
        meta_description=data["meta_description"],
        employment_type=data["employment_type"],
        location=data["location"],
        date_posted=data["date_posted"],
        company_id=company_id,
    )

    if job_id is None:
        return "skipped"

    if data["category"]:
        tag_id = db.get_or_create_tag(data["category"])
        db.attach_tag(job_id, tag_id)

    return "inserted"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(pages: int = 1, limit: int = 100):
    """
    Scrape kariera.gr and store results in the database.

    Args:
        pages: Number of list pages to process.
        limit: Job listings per page (max 100).
    """
    config = dotenv_values(Path(__file__).parent.parent / ".env")
    db_config = {
        "host": config["DB_HOST"],
        "database": config["DB_DATABASE"],
        "user": config["DB_USER"],
        "password": config["DB_PASSWORD"],
        "port": config.get("DB_PORT", 5432),
    }

    session = requests.Session()

    job_urls = collect_job_urls(pages=pages, limit=limit, session=session)
    print(f"\nCollected {len(job_urls)} unique job URLs. Starting detail scrape...\n")

    successful = 0
    skipped = 0
    failed = 0

    with OJADBHandler(db_config) as db:
        for i, url in enumerate(job_urls, start=1):
            print(f"[{i}/{len(job_urls)}] {url}")
            data = parse_job_page(url, session)

            if data is None:
                failed += 1
                time.sleep(REQUEST_DELAY)
                continue

            # Upsert company
            company_id = None
            if data["company"].get("name"):
                company_id = db.get_or_create_company(
                    name=data["company"]["name"],
                    website_url=data["company"].get("website_url"),
                )

            # Insert job posting
            job_id = db.insert_job_posting(
                source_url=data["source_url"],
                source_id=data["source_id"],
                source_name=data["source_name"],
                title=data["title"],
                description_html=data["description_html"],
                description_text=data["description_text"],
                meta_description=data["meta_description"],
                employment_type=data["employment_type"],
                location=data["location"],
                date_posted=data["date_posted"],
                company_id=company_id,
            )

            if job_id is None:
                # ON CONFLICT DO NOTHING — posting already in DB
                skipped += 1
                print("  → already in DB, skipped")
            else:
                # Attach category as a tag
                if data["category"]:
                    tag_id = db.get_or_create_tag(data["category"])
                    db.attach_tag(job_id, tag_id)
                successful += 1
                print(f"  ✓ Inserted (id={job_id})")

            time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 50)
    print(f"  Inserted : {successful}")
    print(f"  Skipped  : {skipped}  (already in DB)")
    print(f"  Failed   : {failed}")
    print(f"  Total    : {len(job_urls)}")
    print("=" * 50)
