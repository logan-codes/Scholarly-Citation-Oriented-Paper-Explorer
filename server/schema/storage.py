from pydantic import BaseModel

class StorageRequest(BaseModel):
    year :int
    per_page: int

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None  

class SuccessfulResponse:
    ingested: int
    