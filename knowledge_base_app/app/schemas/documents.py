from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a document in the knowledge base"""
    
    title: str = Field(..., description="Document title")
    source_type: str = Field(..., description="Type of document (pdf, text, url)")
    source_path: str = Field(..., description="Path or URL of the document")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    department: Optional[str] = None
    status: str = Field(default="active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Legal Compliance Guidelines 2024",
                "source_type": "pdf",
                "source_path": "data/pdfs/legal/compliance_2024.pdf",
                "tags": ["legal", "compliance", "guidelines"],
                "category": "legal",
                "version": "1.0",
                "author": "Legal Department",
                "department": "Legal",
                "status": "active"
            }
        } 