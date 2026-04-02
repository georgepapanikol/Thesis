from __future__ import annotations

from typing import Dict, List, Optional

from backend.database import get_oja_conn
from backend.models.oja_models import (
    CompanyOut,
    EmploymentTypeOption,
    JobDetail,
    JobListItem,
    JobPage,
)

# ---------------------------------------------------------------------------
# Employment type normalisation
# Maps every raw DB value to a canonical human-readable label.
# Values that share a label are treated as equivalent when filtering.
# ---------------------------------------------------------------------------

EMPLOYMENT_TYPE_MAP: Dict[str, str] = {
    "Full Time":            "Full Time",
    "FULL_TIME":            "Full Time",
    "Part Time":            "Part Time",
    "PART_TIME":            "Part Time",
    "FULL_TIME_PART_TIME":  "Full or Part Time",
    "Contractor":           "Contractor",
    "Intern":               "Intern",
    "SEASONAL":             "Seasonal",
    "Other":                "Other",
}

# Reverse: canonical label → list of raw DB values
def _raw_values_for_label(label: str) -> List[str]:
    return [raw for raw, lbl in EMPLOYMENT_TYPE_MAP.items() if lbl == label]


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def fetch_jobs(
    limit: int,
    offset: int,
    search: Optional[str],
    order_col: str,
    order_dir: str,
    employment_type: Optional[str] = None,
) -> JobPage:
    conditions: list[str] = []
    params: list = []

    if search:
        conditions.append("jp.title ILIKE %s")
        params.append(f"%{search}%")
    if employment_type:
        raw_values = _raw_values_for_label(employment_type)
        if not raw_values:
            raw_values = [employment_type]
        placeholders = ", ".join(["%s"] * len(raw_values))
        conditions.append(f"jp.employment_type IN ({placeholders})")
        params.extend(raw_values)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_oja_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) as total FROM job_postings jp {where}",
                params,
            )
            total: int = cur.fetchone()["total"]

            cur.execute(
                f"""
                SELECT jp.id, jp.title, c.name as company_name, jp.employment_type,
                       jp.location, jp.date_posted, jp.source_name
                FROM job_postings jp
                LEFT JOIN companies c ON c.id = jp.company_id
                {where}
                ORDER BY {order_col} {order_dir} NULLS LAST
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    active_filters: dict = {}
    if search:
        active_filters["search"] = search
    if employment_type:
        active_filters["employment_type"] = employment_type

    return JobPage(
        total=total,
        limit=limit,
        offset=offset,
        filters=active_filters,
        sort_by=order_col.replace("jp.", ""),
        sort_order=order_dir.lower(),
        items=[JobListItem(**dict(r)) for r in rows],
    )


def fetch_job(job_id: int) -> Optional[JobDetail]:
    conn = get_oja_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT jp.*, c.name as company_name,
                       COALESCE(
                           ARRAY_AGG(t.name ORDER BY t.name) FILTER (WHERE t.name IS NOT NULL),
                           ARRAY[]::text[]
                       ) as tags
                FROM job_postings jp
                LEFT JOIN companies c ON c.id = jp.company_id
                LEFT JOIN job_posting_tags jpt ON jpt.job_posting_id = jp.id
                LEFT JOIN tags t ON t.id = jpt.tag_id
                WHERE jp.id = %s
                GROUP BY jp.id, c.name
                """,
                (job_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    return JobDetail(**dict(row)) if row else None


# ---------------------------------------------------------------------------
# Employment types
# ---------------------------------------------------------------------------

def fetch_employment_types() -> List[EmploymentTypeOption]:
    conn = get_oja_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT employment_type
                FROM job_postings
                WHERE employment_type IS NOT NULL
                ORDER BY employment_type
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    # Deduplicate by canonical label, preserving order of first occurrence
    seen: dict[str, int] = {}  # label → count
    for row in rows:
        raw = row["employment_type"]
        label = EMPLOYMENT_TYPE_MAP.get(raw, raw)
        seen[label] = seen.get(label, 0) + 1

    return [EmploymentTypeOption(label=label) for label in seen]


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

def fetch_companies() -> List[CompanyOut]:
    conn = get_oja_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM companies ORDER BY name")
            rows = cur.fetchall()
    finally:
        conn.close()

    return [CompanyOut(**dict(r)) for r in rows]
