from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pagination base
# ---------------------------------------------------------------------------

class Pagination(BaseModel):
    """
    Envelope returned by every list endpoint.
    Concrete response models inherit from this and add a typed `items` field.
    """
    total: int = Field(..., description="Total number of records matching the query")
    limit: int = Field(..., description="Maximum number of items returned in this page")
    offset: int = Field(..., description="Number of items skipped before this page")
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Active filter parameters echoed back from the request",
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field used to sort the results",
    )
    sort_order: Optional[str] = Field(
        None,
        description="Sort direction: 'asc' or 'desc'",
    )


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    detail: str
