from pydantic import BaseModel
from typing import List, Dict

class StorageRequest(BaseModel):
    year :int
    per_page: int

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None  

class SuccessfulResponse(BaseModel):
    ingested: int
    papers: List[Dict]
    