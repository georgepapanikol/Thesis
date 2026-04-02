from __future__ import annotations

from typing import List, Optional

from backend.database import get_esco_conn
from backend.models.esco_models import (
    IscoGroupOut,
    IscoGroupDetail,
    OccupationBroaderRef,
    OccupationDetail,
    OccupationListItem,
    OccupationPage,
    OccupationSkillRef,
    SkillBroaderRef,
    SkillDetail,
    SkillGroupRef,
    SkillListItem,
    SkillPage,
)


# ---------------------------------------------------------------------------
# Occupations
# ---------------------------------------------------------------------------

def fetch_occupations(
    limit: int,
    offset: int,
    search: Optional[str],
    order_col: str,
    order_dir: str,
) -> OccupationPage:
    where = "WHERE o.preferred_label ILIKE %s" if search else ""
    params_count = (f"%{search}%",) if search else ()
    params_list = (f"%{search}%", limit, offset) if search else (limit, offset)

    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) as total FROM occupations o {where}",
                params_count,
            )
            total: int = cur.fetchone()["total"]

            cur.execute(
                f"""
                SELECT o.id, o.preferred_label, o.code, o.status
                FROM occupations o
                {where}
                ORDER BY o.{order_col} {order_dir}
                LIMIT %s OFFSET %s
                """,
                params_list,
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return OccupationPage(
        total=total,
        limit=limit,
        offset=offset,
        filters={"search": search} if search else {},
        sort_by=order_col,
        sort_order=order_dir.lower(),
        items=[OccupationListItem(**dict(r)) for r in rows],
    )


def fetch_occupation(occupation_id: int) -> Optional[OccupationDetail]:
    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            # Core occupation row + ISCO group label
            cur.execute(
                """
                SELECT
                    o.id, o.preferred_label, o.alt_labels, o.hidden_labels,
                    o.status, o.modified_date, o.code, o.nace_code,
                    o.green_share, o.url,
                    o.isco_group_id, ig.preferred_label AS isco_group_label,
                    o.regulated_profession_note, o.scope_note,
                    o.definition, o.description
                FROM occupations o
                LEFT JOIN isco_groups ig ON ig.id = o.isco_group_id
                WHERE o.id = %s
                """,
                (occupation_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            # Broader occupations
            cur.execute(
                """
                SELECT ob.broader_occupation_id AS occupation_id,
                       bo.preferred_label, bo.code
                FROM occupation_broader ob
                JOIN occupations bo ON bo.id = ob.broader_occupation_id
                WHERE ob.occupation_id = %s
                ORDER BY bo.preferred_label
                """,
                (occupation_id,),
            )
            broader = [OccupationBroaderRef(**dict(r)) for r in cur.fetchall()]

            # Skills (essential + optional)
            cur.execute(
                """
                SELECT osr.skill_id, s.preferred_label, osr.type AS relation_type
                FROM occupation_skill_relations osr
                JOIN skills s ON s.id = osr.skill_id
                WHERE osr.occupation_id = %s
                ORDER BY osr.type, s.preferred_label
                """,
                (occupation_id,),
            )
            skill_rows = cur.fetchall()

    finally:
        conn.close()

    essential = [OccupationSkillRef(**dict(r)) for r in skill_rows if r["relation_type"] == "essential"]
    optional  = [OccupationSkillRef(**dict(r)) for r in skill_rows if r["relation_type"] == "optional"]

    return OccupationDetail(
        **{k: v for k, v in dict(row).items() if k in OccupationDetail.model_fields},
        broader_occupations=broader,
        essential_skills=essential,
        optional_skills=optional,
    )


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def fetch_skills(
    limit: int,
    offset: int,
    search: Optional[str],
    skill_type: Optional[str],
    order_col: str,
    order_dir: str,
) -> SkillPage:
    conditions: list[str] = []
    params: list = []

    if search:
        conditions.append("preferred_label ILIKE %s")
        params.append(f"%{search}%")
    if skill_type:
        conditions.append("type = %s")
        params.append(skill_type)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as total FROM skills {where}", params)
            total: int = cur.fetchone()["total"]

            cur.execute(
                f"""
                SELECT id, type, reuse_level, preferred_label, status
                FROM skills
                {where}
                ORDER BY {order_col} {order_dir}
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
    if skill_type:
        active_filters["type"] = skill_type

    return SkillPage(
        total=total,
        limit=limit,
        offset=offset,
        filters=active_filters,
        sort_by=order_col,
        sort_order=order_dir.lower(),
        items=[SkillListItem(**dict(r)) for r in rows],
    )


def fetch_skill(skill_id: int) -> Optional[SkillDetail]:
    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            # Core skill row
            cur.execute(
                """
                SELECT id, preferred_label, alt_labels, hidden_labels,
                       type, reuse_level, status, modified_date, url,
                       scope_note, definition, description
                FROM skills
                WHERE id = %s
                """,
                (skill_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            # Broader skills
            cur.execute(
                """
                SELECT sb.broader_skill_id AS skill_id, s.preferred_label
                FROM skill_broader sb
                JOIN skills s ON s.id = sb.broader_skill_id
                WHERE sb.skill_id = %s
                ORDER BY s.preferred_label
                """,
                (skill_id,),
            )
            broader_skills = [SkillBroaderRef(**dict(r)) for r in cur.fetchall()]

            # Skill groups
            cur.execute(
                """
                SELECT sbg.skill_group_id, sg.preferred_label, sg.code
                FROM skill_broader_groups sbg
                JOIN skill_groups sg ON sg.id = sbg.skill_group_id
                WHERE sbg.skill_id = %s
                ORDER BY sg.preferred_label
                """,
                (skill_id,),
            )
            skill_groups = [SkillGroupRef(**dict(r)) for r in cur.fetchall()]

            # Collections (green, digital, language, …)
            cur.execute(
                """
                SELECT sc.name
                FROM skill_collection_relations scr
                JOIN skill_collections sc ON sc.id = scr.collection_id
                WHERE scr.skill_id = %s
                ORDER BY sc.name
                """,
                (skill_id,),
            )
            collections = [r["name"] for r in cur.fetchall()]

    finally:
        conn.close()

    return SkillDetail(
        **dict(row),
        broader_skills=broader_skills,
        skill_groups=skill_groups,
        collections=collections,
    )


# ---------------------------------------------------------------------------
# ISCO Groups
# ---------------------------------------------------------------------------

def fetch_isco_group(isco_group_id: int) -> Optional[IscoGroupDetail]:
    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, url, preferred_label, status, alt_labels,
                       description, broader_isco_group_id, green_share
                FROM isco_groups
                WHERE id = %s
                """,
                (isco_group_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            cur.execute(
                """
                SELECT id, preferred_label, code, status
                FROM occupations
                WHERE isco_group_id = %s
                ORDER BY preferred_label
                """,
                (isco_group_id,),
            )
            occupations = [OccupationListItem(**dict(r)) for r in cur.fetchall()]
    finally:
        conn.close()

    return IscoGroupDetail(
        **dict(row),
        occupations=occupations,
    )


def fetch_isco_groups() -> List[IscoGroupOut]:
    conn = get_esco_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, preferred_label, status, alt_labels,
                       description, broader_isco_group_id, green_share, url
                FROM isco_groups
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [IscoGroupOut(**dict(r)) for r in rows]