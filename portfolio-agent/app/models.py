from typing import List, Dict, Any
from pydantic import BaseModel

class UpsertRequest(BaseModel):
    id: str
    text: str
    meta: Dict[str, Any] = {}

class SearchRequest(BaseModel):
    q: str
    k: int = 4

class GenRequest(BaseModel):
    name: str
    role: str
    color: str
    sections: List[str]
    style: str
    extra: str = ""
    max_tokens: int = 512

class GeneratedFile(BaseModel):
    path: str
    content: str

class GeneratedSite(BaseModel):
    meta: Dict[str, str]
    files: List[GeneratedFile]
    accessibility_issues: List[str] = []
