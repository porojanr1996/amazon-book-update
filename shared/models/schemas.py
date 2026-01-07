"""
Pydantic models for API responses
Maintains backward compatibility with Flask JSON responses
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BSRHistoryEntry(BaseModel):
    """BSR history entry for a single date"""
    date: str
    bsr: int


class Book(BaseModel):
    """Book model"""
    name: str
    author: str
    amazon_link: str
    category: Optional[str] = None
    bsr_history: List[BSRHistoryEntry] = Field(default_factory=list)
    current_bsr: Optional[int] = None
    cover_image: Optional[str] = None

    class Config:
        # Allow extra fields for backward compatibility
        extra = "allow"


class ChartData(BaseModel):
    """Chart data response"""
    dates: List[str] = Field(default_factory=list)
    average_bsr: List[Optional[float]] = Field(default_factory=list)
    books: List[Dict[str, Any]] = Field(default_factory=list)
    total_books: Optional[int] = None
    worksheet: Optional[str] = None

    class Config:
        extra = "allow"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str


class SuccessResponse(BaseModel):
    """Success response"""
    status: str
    message: str
    worksheet: Optional[str] = None
    job_id: Optional[str] = None


class JobProgress(BaseModel):
    """Job progress information"""
    current: int
    total: int
    percentage: float


class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    state: str  # PENDING, PROGRESS, SUCCESS, FAILURE
    status: str
    progress: Optional[JobProgress] = None
    worksheet: Optional[str] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    info: Optional[Dict[str, Any]] = None


class SchedulerStatus(BaseModel):
    """Scheduler status response"""
    running: bool
    next_run: Optional[str] = None
    jobs: List[Dict[str, Any]] = Field(default_factory=list)
