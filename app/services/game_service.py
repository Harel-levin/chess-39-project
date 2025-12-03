"""
Game service layer integrating chess39-core with database and cache.
"""

import sys
import os
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

# Add chess39-core to path
chess_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../chess39-core'))
sys.path.insert(0, chess_core_path)

from game import Game
from pieces import PieceType
from app.db.models import GameModel, Move, User
from app.schemas.game import MoveResponse
from app.services.redis_client import cache_game_state, get_cached_game_state, publish_game_update


def create_game(white_player_id: UUID, black_player_id: UUID, db: Session) -> GameModel:
    """
    Create a new Chess 39 game.
    
    Args:
        white_player_id: White player's user ID
        black_player_id: Black player's user ID
        db: Database session
        
    Returns:
        Created GameModel instance
    """
    # Create game object using chess39-core
    game = Game(str(white_player_id), str(black_player_id))
    game.start_game()
    
    # Get initial state
    initial_state = game.get_state()
    
    # Create database record
    db_game = GameModel(
        white_player_id=white_player_id,
        black_player_id=black_player_id,
        initial_setup_json=initial_state,
        current_state_json=initial_state,
        status="ongoing"
    )
    
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    
    # Cache in Redis
    cache_game_state(str(db_game.id), initial_state)
    
    return db_game


def load_game(game_id: UUID, db: Session) -> Optional[Game]:
    """
    Load game from cache or database.
    
    Returns:
        Game object from chess39-core or None if not found
    """
    # Try cache first (hot path)
    cached = get_cached_game_state(str(game_id))
    if cached:
        return Game.from_state(cached)
    
    # Fallback to database (cold path)
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        return None
    
    # Load and cache
    game = Game.from_state(db_game.current_state_json)
    cache_game_state(str(game_id), db_game.current_state_json)
    
    return game


def make_move(
    game_id: UUID,
    from_square: str,
    to_square: str,
    player_id: UUID,
    promotion_piece: Optional[str],
    db: Session
) -> MoveResponse:
    """
    Process a move in a game.
    
    Args:
        game_id: Game ID
        from_square: Starting square (e.g., "e2")
        to_square: Destination square (e.g., "e4")
        player_id: Player making the move
        promotion_piece: Pawn promotion piece if applicable
        db: Database session
        
    Returns:
        MoveResponse with success status and details
    """
    # Load game
    game = load_game(game_id, db)
    if not game:
        return MoveResponse(
            success=False,
            message="Game not found",
            status="not_found"
        )
    
    # Convert promotion piece string to PieceType if provided
    promo_piece_type = None
    if promotion_piece:
        promo_piece_type = PieceType[promotion_piece]
    
    # Attempt move using chess39-core
    result = game.make_move(from_square, to_square, str(player_id), promo_piece_type)
    
    if not result['success']:
        return MoveResponse(
            success=False,
            message=result['message'],
            status=game.status
        )
    
    # Move successful - update database
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    
    # Save move to database
    move_record = Move(
        game_id=game_id,
        move_number=game.fullmove_number,
        color=game.current_turn,  # This is now the opponent's turn (after move)
        from_square=from_square,
        to_square=to_square,
        piece_type=game.move_history[-1]['piece'],
        captured_piece=result.get('captured'),
        is_check=result.get('is_check', False),
        is_checkmate=(result['status'] == 'checkmate')
    )
    
    db.add(move_record)
    
    # Update game state
    new_state = game.get_state()
    db_game.current_state_json = new_state
    db_game.status = game.status
    
    # Handle game completion
    if game.status in ['checkmate', 'stalemate', 'draw']:
        db_game.winner_id = UUID(game.winner) if game.winner else None
        from datetime import datetime
        db_game.completed_at = datetime.utcnow()
        
        # Update player stats and ELO
        if game.status == 'checkmate':
            update_elo_ratings(db_game, db)
    
    db.commit()
    
    # Update cache
    cache_game_state(str(game_id), new_state)
    
    # Publish update via Redis pub/sub
    publish_game_update(str(game_id), {
        'type': 'move_made',
        'move': {
            'from': from_square,
            'to': to_square,
            'captured': result.get('captured')
        },
        'game_state': new_state
    })
    
    return MoveResponse(
        success=True,
        message="Move successful",
        captured=result.get('captured'),
        is_check=result.get('is_check', False),
        is_checkmate=(result['status'] == 'checkmate'),
        status=game.status
    )


def update_elo_ratings(game: GameModel, db: Session):
    """
    Update ELO ratings for both players after game completion.
    
    Uses standard ELO formula with K-factor of 32.
    """
    white = db.query(User).filter(User.id == game.white_player_id).first()
    black = db.query(User).filter(User.id == game.black_player_id).first()
    
    # Determine outcome (1 = white wins, 0 = black wins, 0.5 = draw)
    if game.winner_id == game.white_player_id:
        white_score = 1.0
        black_score = 0.0
        white.wins += 1
        black.losses += 1
    elif game.winner_id == game.black_player_id:
        white_score = 0.0
        black_score = 1.0
        white.losses += 1
        black.wins += 1
    else:  # Draw
        white_score = 0.5
        black_score = 0.5
        white.draws += 1
        black.draws += 1
    
    # Calculate expected scores
    white_expected = 1 / (1 + 10 ** ((black.elo_rating - white.elo_rating) / 400))
    black_expected = 1 / (1 + 10 ** ((white.elo_rating - black.elo_rating) / 400))
    
    # Update ratings (K = 32)
    K = 32
    white.elo_rating += int(K * (white_score - white_expected))
    black.elo_rating += int(K * (black_score - black_expected))
    
    # Update game counts
    white.games_played += 1
    black.games_played += 1
    
    db.commit()
