from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class ScrapeConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    start_url: str = Field(..., min_length=1)
    css_selector: str = Field(..., min_length=1)
    region: str = Field(default="US", max_length=50)
    proxy_enabled: bool = Field(default=False)
    schedule_cron: str = Field(..., min_length=1, max_length=100)
    gemini_prompt: str = Field(..., min_length=1)
    gemini_model: str = Field(default="gemini-pro", max_length=100)
    active: bool = Field(default=True)
    wait_time: int = Field(default=5, ge=0, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=30, ge=5, le=300)
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class ScrapeConfigCreate(ScrapeConfigBase):
    pass


class ScrapeConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_url: Optional[str] = Field(None, min_length=1)
    css_selector: Optional[str] = Field(None, min_length=1)
    region: Optional[str] = Field(None, max_length=50)
    proxy_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = Field(None, min_length=1, max_length=100)
    gemini_prompt: Optional[str] = Field(None, min_length=1)
    gemini_model: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    wait_time: Optional[int] = Field(None, ge=0, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    extra_config: Optional[Dict[str, Any]] = None


class ScrapeConfig(ScrapeConfigBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


class ScrapeResultBase(BaseModel):
    status: str
    error_message: Optional[str] = None
    extracted_data: Optional[Any] = None
    gemini_response: Optional[Dict[str, Any]] = None
    gemini_cost: Optional[float] = None
    gemini_model_used: Optional[str] = None


class ScrapeResult(ScrapeResultBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    config_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class ScrapeResultsResponse(BaseModel):
    results: List[ScrapeResult]
    total: int
    page: int
    size: int


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ScrapeJobTrigger(BaseModel):
    config_id: int
    run_immediately: bool = Field(default=True)