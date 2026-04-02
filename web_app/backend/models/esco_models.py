from __future__ import annotations
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from backend.models.generic import Pagination


# ---------------------------------------------------------------------------
# ESCO – ISCO Groups
# ---------------------------------------------------------------------------

class IscoGroupOut(BaseModel):
    id: str
    preferred_label: str
    status: Optional[str] = None
    alt_labels: Optional[str] = None
    description: Optional[str] = None
    broader_isco_group_id: Optional[str] = None
    green_share: Optional[float] = None
    url: Optional[str] = None
    occupations: List[OccupationListItem] = Field(default_factory=list)


class IscoGroupDetail(BaseModel):
    id: str
    url: str
    preferred_label: str
    status: Optional[str] = None
    alt_labels: Optional[str] = None
    description: Optional[str] = None
    broader_isco_group_id: Optional[str] = None
    green_share: Optional[float] = None
    occupations: List[OccupationListItem] = Field(default_factory=list)



# ---------------------------------------------------------------------------
# ESCO – Occupations
# ---------------------------------------------------------------------------

class OccupationSkillRef(BaseModel):
    skill_id: int
    preferred_label: str
    relation_type: Optional[str] = None   # 'essential' | 'optional'


class OccupationBroaderRef(BaseModel):
    occupation_id: int
    preferred_label: str
    code: Optional[str] = None


class OccupationListItem(BaseModel):
    id: int
    preferred_label: str
    code: Optional[str] = None
    status: Optional[str] = None


class OccupationPage(Pagination):
    items: List[OccupationListItem] = Field(..., description="Occupation records for this page")


class OccupationDetail(BaseModel):
    id: int
    preferred_label: str
    alt_labels: Optional[str] = None
    hidden_labels: Optional[str] = None
    status: Optional[str] = None
    modified_date: Optional[date] = None
    code: Optional[str] = None
    nace_code: Optional[str] = None
    green_share: Optional[float] = None
    url: Optional[str] = None
    isco_group_id: Optional[str] = None
    isco_group_label: Optional[str] = None
    regulated_profession_note: Optional[str] = None
    scope_note: Optional[str] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    # Relations
    broader_occupations: List[OccupationBroaderRef] = Field(default_factory=list)
    essential_skills: List[OccupationSkillRef] = Field(default_factory=list)
    optional_skills: List[OccupationSkillRef] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ESCO – Skills
# ---------------------------------------------------------------------------

class SkillBroaderRef(BaseModel):
    skill_id: int
    preferred_label: str


class SkillGroupRef(BaseModel):
    skill_group_id: int
    preferred_label: str
    code: Optional[str] = None


class SkillListItem(BaseModel):
    id: int
    preferred_label: str
    type: Optional[str] = None
    reuse_level: Optional[str] = None
    status: Optional[str] = None


class SkillPage(Pagination):
    items: List[SkillListItem] = Field(..., description="Skill records for this page")


class SkillDetail(BaseModel):
    id: int
    preferred_label: str
    alt_labels: Optional[str] = None
    hidden_labels: Optional[str] = None
    type: Optional[str] = None
    reuse_level: Optional[str] = None
    status: Optional[str] = None
    modified_date: Optional[date] = None
    url: Optional[str] = None
    scope_note: Optional[str] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    # Relations
    broader_skills: List[SkillBroaderRef] = Field(default_factory=list)
    skill_groups: List[SkillGroupRef] = Field(default_factory=list)
    collections: List[str] = Field(default_factory=list)