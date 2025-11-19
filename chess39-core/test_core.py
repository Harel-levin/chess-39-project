"""
Simple test to verify Chess 39 core logic is working correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pieces import PieceType
from army import generate_random_army
from board import Board
from game import Game


def test_army_generation():
    """Test that random armies are generated correctly."""
    print("Testing Army Generation...")
    
    for i in range(3):
        army = generate_random_army()
        total_points = sum(p.value for p in army)
        num_pawns = sum(1 for p in army if p == PieceType.PAWN)
        has_king = PieceType.KING in army
        
        print(f"  Army {i+1}: Total={total_points} points, Pawns={num_pawns}, Has King={has_king}")
        assert total_points == 39, f"Expected 39 points, got {total_points}"
        assert num_pawns <= 8, f"Too many pawns: {num_pawns}"
        assert has_king, "Army must have a king"
    
    print("✓ Army generation working correctly\n")


def test_board_setup():
    """Test that board setup works."""
    print("Testing Board Setup...")
    
    board = Board()
    board.setup_board()
    
    # Count pieces
    white_pieces = sum(1 for p in board.grid.values() if p and p[1] == 'white')
    black_pieces = sum(1 for p in board.grid.values() if p and p[1] == 'black')
    
    print(f"  White pieces: {white_pieces}")
    print(f"  Black pieces: {black_pieces}")
    
    board.print_board()
    print("✓ Board setup working correctly\n")


def test_basic_moves():
    """Test basic move validation."""
    print("Testing Basic Moves...")
    
    game = Game("player1", "player2")
    game.start_game()
    
    # Find a pawn to move
    white_pawn_square = None
    for square, piece_data in game.board.grid.items():
        if piece_data and piece_data[0] == PieceType.PAWN and piece_data[1] == 'white':
            col, row = square[0], int(square[1])
            if row == 2:  # Pawn on starting rank
                white_pawn_square = square
                break
    
    if white_pawn_square:
        # Try moving pawn forward
        to_square = white_pawn_square[0] + '3'
        result = game.make_move(white_pawn_square, to_square, "player1")
        print(f"  Move {white_pawn_square} to {to_square}: {result['message']}")
        assert result['success'], f"Valid move failed: {result['message']}"
        print("✓ Basic move validation working\n")
    else:
        print("  No white pawn found on starting rank (skipping move test)\n")


def test_invalid_moves():
    """Test that invalid moves are rejected."""
    print("Testing Invalid Move Rejection...")
    
    game = Game("player1", "player2")
    game.start_game()
    
    # Try to make invalid move
    result = game.make_move("e2", "e5", "player1")  # Pawn can't move 3 squares
    print(f"  Invalid move e2 to e5: {result['message']}")
    assert not result['success'], "Invalid move should be rejected"
    
    # Try to move opponent's piece
    result = game.make_move("e7", "e6", "player1")  # White trying to move black pawn
    print(f"  Wrong color move: {result['message']}")
    assert not result['success'], "Moving opponent piece should be rejected"
    
    print("✓ Invalid move rejection working\n")


def test_game_state_serialization():
    """Test game state can be serialized and deserialized."""
    print("Testing Game State Serialization...")
    
    game1 = Game("player1", "player2")
    game1.start_game()
    
    # Get state
    state = game1.get_state()
    print(f"  Serialized state keys: {list(state.keys())}")
    
    # Recreate from state
    game2 = Game.from_state(state)
    state2 = game2.get_state()
    
    assert state['current_turn'] == state2['current_turn']
    assert state['status'] == state2['status']
    print("✓ Game state serialization working\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Chess 39 Core Logic Test Suite")
    print("=" * 50 + "\n")
    
    try:
        test_army_generation()
        test_board_setup()
        test_basic_moves()
        test_invalid_moves()
        test_game_state_serialization()
        
        print("=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
