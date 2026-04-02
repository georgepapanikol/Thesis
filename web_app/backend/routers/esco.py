from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models.esco_models import (
    IscoGroupOut,
    OccupationDetail,
    OccupationPage,
    SkillDetail,
    SkillPage,
    IscoGroupDetail,
)
from backend.models.generic import ErrorDetail
from backend.services.esco_service import (
    fetch_isco_groups,
    fetch_isco_group,
    fetch_occupation,
    fetch_occupations,
    fetch_skill,
    fetch_skills,
)

router = APIRouter()

_OCC_SORT  = {"preferred_label", "code", "status"}
_SKILL_SORT = {"preferred_label", "type", "reuse_level", "status"}


# ---------------------------------------------------------------------------
# Occupations
# ---------------------------------------------------------------------------

@router.get(
    "/occupations",
    response_model=OccupationPage,
    responses={500: {"model": ErrorDetail}},
)
def list_occupations(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, description="preferred_label | code | status"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
) -> OccupationPage:
    order_col = sort_by if sort_by in _OCC_SORT else "preferred_label"
    order_dir = "DESC" if sort_order == "desc" else "ASC"
    try:
        return fetch_occupations(limit, offset, search, order_col, order_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/occupations/{occupation_id}",
    response_model=OccupationDetail,
    responses={
        404: {"model": ErrorDetail},
        500: {"model": ErrorDetail},
    },
)
def get_occupation(occupation_id: int) -> OccupationDetail:
    try:
        result = fetch_occupation(occupation_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Occupation not found")
    return result


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@router.get(
    "/skills",
    response_model=SkillPage,
    responses={500: {"model": ErrorDetail}},
)
def list_skills(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    skill_type: Optional[str] = Query(None, alias="type"),
    sort_by: Optional[str] = Query(None, description="preferred_label | type | reuse_level | status"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
) -> SkillPage:
    order_col = sort_by if sort_by in _SKILL_SORT else "preferred_label"
    order_dir = "DESC" if sort_order == "desc" else "ASC"
    try:
        return fetch_skills(limit, offset, search, skill_type, order_col, order_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/skills/{skill_id}",
    response_model=SkillDetail,
    responses={
        404: {"model": ErrorDetail},
        500: {"model": ErrorDetail},
    },
)
def get_skill(skill_id: int) -> SkillDetail:
    try:
        result = fetch_skill(skill_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return result


# ---------------------------------------------------------------------------
# ISCO Groups
# ---------------------------------------------------------------------------

@router.get(
    "/isco_groups",
    response_model=List[IscoGroupOut],
    responses={500: {"model": ErrorDetail}},
)
def list_isco_groups() -> List[IscoGroupOut]:
    try:
        return fetch_isco_groups()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get(
    "/isco_groups/{isco_group_id}",
    response_model= IscoGroupDetail,
    responses={
        404: {"model": ErrorDetail},
        500: {"model": ErrorDetail},
    },
)

def get_isco_group(isco_group_id: int) -> IscoGroupDetail:
    try:
        result = fetch_isco_group(isco_group_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Isco Group not found")
    return result

