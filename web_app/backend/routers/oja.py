from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.models.generic import ErrorDetail
from backend.models.oja_models import (
    CompanyOut,
    EmploymentTypeOption,
    JobDetail,
    JobPage,
)
from backend.services.oja_service import (
    fetch_companies,
    fetch_employment_types,
    fetch_job,
    fetch_jobs,
)

router = APIRouter()

_JOB_SORT = {"title", "location", "date_posted", "employment_type"}


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.get(
    "/jobs",
    response_model=JobPage,
    responses={500: {"model": ErrorDetail}},
)
def list_jobs(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, description="title | location | date_posted | employment_type"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    employment_type: Optional[str] = None,
) -> JobPage:
    order_col = f"jp.{sort_by}" if sort_by in _JOB_SORT else "jp.date_posted"
    order_dir = "ASC" if sort_order == "asc" else "DESC"
    try:
        return fetch_jobs(limit, offset, search, order_col, order_dir, employment_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Employment types  (must be before /{job_id} to avoid 422)
# ---------------------------------------------------------------------------

@router.get(
    "/jobs/employment_types",
    response_model=List[EmploymentTypeOption],
    responses={500: {"model": ErrorDetail}},
)
def list_employment_types() -> List[EmploymentTypeOption]:
    try:
        return fetch_employment_types()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/jobs/{job_id}",
    response_model=JobDetail,
    responses={
        404: {"model": ErrorDetail},
        500: {"model": ErrorDetail},
    },
)
def get_job(job_id: int) -> JobDetail:
    try:
        result = fetch_job(job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

@router.get(
    "/companies",
    response_model=List[CompanyOut],
    responses={500: {"model": ErrorDetail}},
)
def list_companies() -> List[CompanyOut]:
    try:
        return fetch_companies()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc