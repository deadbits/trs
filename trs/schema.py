from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class Document(BaseModel):
    text: str
    embedding: Optional[List[float]] = Field(
        None,
        description="Embedding of the document"
    )
    source: str
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata dict"
    )


class Summary(BaseModel):
    summary: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Optional metadata dict"
    )


class Indicators(BaseModel):
    ips: Optional[List[str]] = Field(
        None,
        description="Optional list of IP addresses"
    )
    urls: Optional[List[str]] = Field(
        None,
        description="Optional list of URLs"
    )
    hashes: Optional[List[str]] = Field(
        None,
        description="Optional list of file hashes"
    )

