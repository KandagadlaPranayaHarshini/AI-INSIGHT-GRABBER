from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any

# --- Auth Schemas ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# --- Analytics Schemas ---
class SummaryStat(BaseModel):
    column: str
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None

class AnalysisResponse(BaseModel):
    dataset_id: int
    filename: str
    rows: int
    columns: int
    missing_values: int
    duplicates: int
    statistics: List[SummaryStat]
    saved_insights: List[dict]
    saved_charts: List[dict]