"""
SQLAlchemy ORM models for Chess 39.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Stats and rating
    elo_rating = Column(Integer, default=1200)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    games_as_white = relationship(
        "GameModel",
        foreign_keys="GameModel.white_player_id",
        back_populates="white_player"
    )
    games_as_black = relationship(
        "GameModel",
        foreign_keys="GameModel.black_player_id",
        back_populates="black_player"
    )
    
    def __repr__(self):
        return f"<User {self.username} (ELO: {self.elo_rating})>"


class GameModel(Base):
    """Game model storing Chess 39 matches."""
    
    __tablename__ = "games"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Players
    white_player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    black_player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Game state (stored as JSON)
    initial_setup_json = Column(JSON, nullable=False)  # Random piece configuration
    current_state_json = Column(JSON, nullable=False)  # Current board state
    
    # Game status
    status = Column(String(20), nullable=False, default="ongoing")  # ongoing, checkmate, stalemate, resignation, draw
    winner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    white_player = relationship(
        "User",
        foreign_keys=[white_player_id],
        back_populates="games_as_white"
    )
    black_player = relationship(
        "User",
        foreign_keys=[black_player_id],
        back_populates="games_as_black"
    )
    winner = relationship("User", foreign_keys=[winner_id])
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Game {self.id} ({self.status})>"


class Move(Base):
    """Individual move in a game."""
    
    __tablename__ = "moves"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    
    # Move details
    move_number = Column(Integer, nullable=False)  # Full move number (increments after black moves)
    color = Column(String(5), nullable=False)  # white or black
    from_square = Column(String(2), nullable=False)  # e.g., "e2"
    to_square = Column(String(2), nullable=False)  # e.g., "e4"
    piece_type = Column(String(10), nullable=False)  # PAWN, KNIGHT, etc.
    captured_piece = Column(String(10), nullable=True)  # Piece that was captured, if any
    promotion_piece = Column(String(10), nullable=True)  # Piece pawn was promoted to, if any
    
    # Special flags
    is_check = Column(Boolean, default=False)
    is_checkmate = Column(Boolean, default=False)
    is_castling = Column(Boolean, default=False)
    is_en_passant = Column(Boolean, default=False)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("GameModel", back_populates="moves")
    
    def __repr__(self):
        return f"<Move {self.move_number}. {self.from_square}-{self.to_square}>"
