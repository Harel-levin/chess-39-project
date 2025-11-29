"""
Pydantic schemas for game-related API endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any


class GameCreate(BaseModel):
    """Schema for creating a new game."""
    opponent_id: Optional[UUID] = None  # If None, use matchmaking


class MoveRequest(BaseModel):
    """Schema for submitting a move."""
    from_square: str = Field(..., min_length=2, max_length=2, pattern="^[a-h][1-8]$")
    to_square: str = Field(..., min_length=2, max_length=2, pattern="^[a-h][1-8]$")
    promotion_piece: Optional[str] = Field(None, pattern="^(QUEEN|ROOK|BISHOP|KNIGHT)$")


class MoveResponse(BaseModel):
    """Schema for move result."""
    success: bool
    message: str
    captured: Optional[str] = None
    is_check: bool = False
    is_checkmate: bool = False
    status: str
    
    class Config:
        from_attributes = True


class PlayerInfo(BaseModel):
    """Player information in game context."""
    id: UUID
    username: str
    elo_rating: int
    
    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    """Full game state response."""
    id: UUID
    white_player: PlayerInfo
    black_player: PlayerInfo
    board: Dict[str, Any]  # Board state (square -> piece)
    current_turn: str  # white or black
    status: str
    winner: Optional[PlayerInfo] = None
    moves: List[Dict[str, Any]]  # Move history
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class GameListItem(BaseModel):
    """Summary for game list."""
    id: UUID
    white_player: PlayerInfo
    black_player: PlayerInfo
    status: str
    winner_id: Optional[UUID]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ValidMovesResponse(BaseModel):
    """Valid moves for a piece."""
    square: str
    valid_moves: List[str]  # List of destination squares
