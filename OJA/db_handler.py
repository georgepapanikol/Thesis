import psycopg2
from typing import Dict, Optional


class OJADBHandler:
    """Handles all database operations for Online Job Advertisements"""

    def __init__(self, db_config: Dict[str, str]):
        """
        Args:
            db_config: Dictionary with keys: host, database, user, password, port
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(
            host=self.db_config['host'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            port=self.db_config.get('port', 5432)
        )
        self.cursor = self.conn.cursor()
        print("✓ Database connection established")

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Database connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------

    def get_or_create_company(self, name: str, website_url: Optional[str]) -> int:
        """Return company id, inserting a new row if needed."""
        self.cursor.execute(
            "SELECT id FROM companies WHERE name = %s",
            (name,)
        )
        row = self.cursor.fetchone()
        if row:
            return row[0]

        self.cursor.execute(
            "INSERT INTO companies (name, website_url) VALUES (%s, %s) RETURNING id",
            (name, website_url)
        )
        company_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return company_id

    # ------------------------------------------------------------------
    # Lookup tables (seniority, categories, parent_categories,
    #                location_restrictions, timezone_restrictions)
    # ------------------------------------------------------------------

    def _get_or_create(self, table: str, column: str, value: str) -> int:
        self.cursor.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute(
            f"INSERT INTO {table} ({column}) VALUES (%s) RETURNING id", (value,)
        )
        return self.cursor.fetchone()[0]

    def get_or_create_seniority(self, name: str) -> int:
        return self._get_or_create("seniority_levels", "name", name)

    def get_or_create_category(self, name: str) -> int:
        return self._get_or_create("categories", "name", name)

    def get_or_create_parent_category(self, name: str) -> int:
        return self._get_or_create("parent_categories", "name", name)

    def get_or_create_location_restriction(self, name: str) -> int:
        return self._get_or_create("location_restrictions", "name", name)

    def get_or_create_timezone_restriction(self, utc_offset: float) -> int:
        self.cursor.execute(
            "SELECT id FROM timezone_restrictions WHERE utc_offset = %s", (utc_offset,)
        )
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute(
            "INSERT INTO timezone_restrictions (utc_offset) VALUES (%s) RETURNING id",
            (utc_offset,)
        )
        return self.cursor.fetchone()[0]

    def attach_seniority(self, job_posting_id: int, seniority_id: int):
        self.cursor.execute(
            "INSERT INTO job_posting_seniority VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (job_posting_id, seniority_id)
        )

    def attach_category(self, job_posting_id: int, category_id: int):
        self.cursor.execute(
            "INSERT INTO job_posting_categories VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (job_posting_id, category_id)
        )

    def attach_parent_category(self, job_posting_id: int, parent_category_id: int):
        self.cursor.execute(
            "INSERT INTO job_posting_parent_categories VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (job_posting_id, parent_category_id)
        )

    def attach_location_restriction(self, job_posting_id: int, location_restriction_id: int):
        self.cursor.execute(
            "INSERT INTO job_posting_location_restrictions VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (job_posting_id, location_restriction_id)
        )

    def attach_timezone_restriction(self, job_posting_id: int, timezone_restriction_id: int):
        self.cursor.execute(
            "INSERT INTO job_posting_timezone_restrictions VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (job_posting_id, timezone_restriction_id)
        )

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def get_or_create_tag(self, name: str) -> int:
        """Return tag id, inserting a new row if needed."""
        self.cursor.execute("SELECT id FROM tags WHERE name = %s", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]

        self.cursor.execute(
            "INSERT INTO tags (name) VALUES (%s) RETURNING id", (name,)
        )
        tag_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return tag_id

    def attach_tag(self, job_posting_id: int, tag_id: int):
        """Link a tag to a job posting (ignore if already linked)."""
        self.cursor.execute(
            """
            INSERT INTO job_posting_tags (job_posting_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (job_posting_id, tag_id)
        )

    # ------------------------------------------------------------------
    # Job postings
    # ------------------------------------------------------------------

    def url_exists(self, source_url: str) -> bool:
        """Return True if a job posting with this URL is already in the DB."""
        self.cursor.execute(
            "SELECT 1 FROM job_postings WHERE source_url = %s LIMIT 1",
            (source_url,)
        )
        return self.cursor.fetchone() is not None

    def insert_job_posting(
        self,
        source_url: str,
        source_id: Optional[str],
        source_name: Optional[str],
        title: str,
        description_html: Optional[str],
        description_text: Optional[str],
        meta_description: Optional[str],
        employment_type: Optional[str],
        location: Optional[str],
        date_posted,
        company_id: Optional[int],
        min_salary: Optional[float]= None,
        max_salary: Optional[float] = None,
        currency: Optional[str] = None,
        date_expires: Optional[str] = None
    ) -> Optional[int]:
        """
        Insert a job posting. Skips silently if source_url already exists.

        Returns:
            The new row id, or None if the posting already existed.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO job_postings (
                    source_url, source_id, source_name,
                    title, description_html, description_text, meta_description,
                    employment_type, location, min_salary, max_salary, currency, date_posted, date_expires, company_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO NOTHING
                RETURNING id
                """,
                (
                    source_url, source_id, source_name,
                    title, description_html, description_text, meta_description,
                    employment_type, location, min_salary, max_salary, currency, date_posted, date_expires, company_id,
                )
            )
            row = self.cursor.fetchone()
            self.conn.commit()
            return row[0] if row else None
        except Exception as e:
            print(f"  ✗ Error inserting job posting {source_url}: {e}")
            self.conn.rollback()
            return None
