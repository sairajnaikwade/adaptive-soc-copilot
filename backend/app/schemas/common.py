"""Common Pydantic response wrappers and shared schema utilities."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """
    Standard success response envelope.

    All successful API responses are wrapped in this envelope to provide
    a consistent structure that frontend code can depend on.

    Example:
        {"success": true, "message": "Tenant created.", "data": {...}}
    """
    success: bool = Field(default=True)
    message: str = Field(default="Operation successful.")
    data: Optional[DataT] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated list response for collection endpoints."""
    success: bool = Field(default=True)
    data: List[DataT]
    total: int = Field(..., description="Total number of records matching the filter.")
    page: int = Field(..., description="Current page number (1-indexed).")
    page_size: int = Field(..., description="Number of records per page.")
    total_pages: int = Field(..., description="Total number of pages.")


class ErrorResponse(BaseModel):
    """Standard error response body."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error description.")
    detail: Optional[object] = Field(default=None, description="Additional error context.")
