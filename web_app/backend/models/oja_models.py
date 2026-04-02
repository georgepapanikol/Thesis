from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.models.generic import Pagination


# ---------------------------------------------------------------------------
# OJA – Companies
# ---------------------------------------------------------------------------

class CompanyOut(BaseModel):
    id: int
    name: str


# ---------------------------------------------------------------------------
# OJA – Employment types
# ---------------------------------------------------------------------------

class EmploymentTypeOption(BaseModel):
    label: str   # canonical human-readable label


# ---------------------------------------------------------------------------
# OJA – Job Postings
# ---------------------------------------------------------------------------

class JobListItem(BaseModel):
    id: int
    title: str
    company_name: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    date_posted: Optional[datetime] = None
    source_name: Optional[str] = None


class JobPage(Pagination):
    items: List[JobListItem] = Field(..., description="Job posting records for this page")


class JobDetail(BaseModel):
    id: int
    title: str
    company_name: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    date_posted: Optional[datetime] = None
    date_expires: Optional[datetime] = None
    date_added: Optional[datetime] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: Optional[str] = None
    description_text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
