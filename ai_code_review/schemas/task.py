"""Task definition schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TaskType(str, Enum):
    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskDefinition(BaseModel):
    """Task definition schema."""
    
    id: str = Field(..., description="Unique task identifier")
    type: TaskType = Field(..., description="Type of task")
    priority: TaskPriority = Field(..., description="Task priority")
    description: str = Field(..., description="Detailed task description")
    requirements: List[str] = Field(
        ...,
        description="List of specific requirements"
    )
    acceptance_criteria: List[str] = Field(
        ...,
        description="List of acceptance criteria"
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="List of dependent task IDs"
    )
    max_iterations: int = Field(
        default=5,
        description="Maximum number of implementation iterations"
    )
    quality_thresholds: dict = Field(
        default_factory=lambda: {
            "code_review": 85,
            "test_coverage": 90,
            "security_score": 95
        },
        description="Quality thresholds for different metrics"
    )

class TaskResult(BaseModel):
    """Task execution result schema."""
    
    task_id: str = Field(..., description="Task ID")
    code: str = Field(..., description="Implemented code")
    iterations: int = Field(..., description="Number of iterations taken")
    review_score: Optional[float] = Field(
        None,
        description="Code review score"
    )
    test_coverage: Optional[float] = Field(
        None,
        description="Test coverage percentage"
    )
    security_score: Optional[float] = Field(
        None,
        description="Security assessment score"
    ) 