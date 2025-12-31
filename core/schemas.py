"""Pydantic schemas for task data."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    """Metadata for a task."""
    id: str
    domain: str
    difficulty: str = "medium"
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskPair(BaseModel):
    """A task pair with initial and final states."""
    task_id: str
    domain: str
    prompt: str
    first_image: Any  # PIL Image
    final_image: Optional[Any] = None  # PIL Image or None
    goal_text: Optional[str] = None  # Text answer or None
    metadata: TaskMetadata
    
    class Config:
        arbitrary_types_allowed = True
