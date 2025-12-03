"""
Pydantic schemas for user-related API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user signup."""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    id: UUID
    elo_rating: int
    games_played: int
    wins: int
    losses: int
    draws: int
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allows creating from ORM models


class UserStats(BaseModel):
    """User statistics."""
    user_id: UUID
    username: str
    elo_rating: int
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token."""
    user_id: UUID
