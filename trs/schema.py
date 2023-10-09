from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class Document(BaseModel):
    text: str
    source: str
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the document"
    )


class Summary(BaseModel):
    summary: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata for the document"
    )


class Indicators(BaseModel):
    ips: List[str]
    urls: List[str]
    hashes: List[str]
