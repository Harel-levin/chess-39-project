"""
Game API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.db.database import get_db
from app.db.models import User, GameModel
from app.schemas.game import GameCreate, GameResponse, MoveRequest, MoveResponse, GameListItem, PlayerInfo, ValidMovesResponse
from app.api.dependencies import get_current_user
from app.services import game_service


router = APIRouter()


@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    game_data: GameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new Chess 39 game.
    
    If opponent_id is provided, creates a direct challenge.
    If not provided, uses matchmaking (not implemented yet).
    """
    if not game_data.opponent_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Matchmaking not yet implemented. Please specify opponent_id."
        )
    
    # Verify opponent exists
    opponent = db.query(User).filter(User.id == game_data.opponent_id).first()
    if not opponent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opponent not found"
        )
    
    # Randomly assign colors (simplified - could be more sophisticated)
    import random
    if random.choice([True, False]):
        white_id, black_id = current_user.id, game_data.opponent_id
    else:
        white_id, black_id = game_data.opponent_id, current_user.id
    
    # Create game
    game = game_service.create_game(white_id, black_id, db)
    
    # Load game state for response
    game_obj = game_service.load_game(game.id, db)
    state = game_obj.get_state()
    
    return GameResponse(
        id=game.id,
        white_player=PlayerInfo(id=game.white_player.id, username=game.white_player.username, elo_rating=game.white_player.elo_rating),
        black_player=PlayerInfo(id=game.black_player.id, username=game.black_player.username, elo_rating=game.black_player.elo_rating),
        board=state['board'],
        current_turn=state['current_turn'],
        status=state['status'],
        moves=state['move_history'],
        created_at=game.created_at,
        started_at=game.started_at,
        completed_at=game.completed_at
    )


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: UUID, db: Session = Depends(get_db)):
    """Get current game state."""
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_obj = game_service.load_game(game_id, db)
    state = game_obj.get_state()
    
    return GameResponse(
        id=db_game.id,
        white_player=PlayerInfo(id=db_game.white_player.id, username=db_game.white_player.username, elo_rating=db_game.white_player.elo_rating),
        black_player=PlayerInfo(id=db_game.black_player.id, username=db_game.black_player.username, elo_rating=db_game.black_player.elo_rating),
        board=state['board'],
        current_turn=state['current_turn'],
        status=state['status'],
        winner=PlayerInfo(id=db_game.winner.id, username=db_game.winner.username, elo_rating=db_game.winner.elo_rating) if db_game.winner else None,
        moves=state['move_history'],
        created_at=db_game.created_at,
        started_at=db_game.started_at,
        completed_at=db_game.completed_at
    )


@router.get("", response_model=List[GameListItem])
def list_games(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's games with optional status filter."""
    query = db.query(GameModel).filter(
        (GameModel.white_player_id == current_user.id) | (GameModel.black_player_id == current_user.id)
    )
    
    if status:
        query = query.filter(GameModel.status == status)
    
    games = query.order_by(GameModel.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        GameListItem(
            id=g.id,
            white_player=PlayerInfo(id=g.white_player.id, username=g.white_player.username, elo_rating=g.white_player.elo_rating),
            black_player=PlayerInfo(id=g.black_player.id, username=g.black_player.username, elo_rating=g.black_player.elo_rating),
            status=g.status,
            winner_id=g.winner_id,
            created_at=g.created_at,
            completed_at=g.completed_at
        )
        for g in games
    ]


@router.post("/{game_id}/move", response_model=MoveResponse)
def make_move(
    game_id: UUID,
    move_data: MoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a move in a game."""
    return game_service.make_move(
        game_id,
        move_data.from_square,
        move_data.to_square,
        current_user.id,
        move_data.promotion_piece,
        db
    )


@router.post("/{game_id}/resign", response_model=dict)
def resign_game(
    game_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resign from a game."""
    game_obj = game_service.load_game(game_id, db)
    if not game_obj:
        raise HTTPException(status_code=404, detail="Game not found")
    
    result = game_obj.resign(str(current_user.id))
    
    if result['success']:
        # Update database
        db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
        db_game.status = 'resignation'
        db_game.winner_id = UUID(game_obj.winner)
        db_game.completed_at = db.query(db.func.now()).scalar()
        
        # Update ELO
        game_service.update_elo_ratings(db_game, db)
        
        db.commit()
    
    return result
