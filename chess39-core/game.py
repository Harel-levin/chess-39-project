"""
Chess 39 Game Logic Module

This module contains the high-level Game class that manages game state,
move validation, and win conditions for Chess 39.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import copy

# Handle imports - work both standalone and when imported
try:
    from pieces import PieceType, get_piece_directions, KNIGHT_MOVES, KING_MOVES
    from board import Board
except ImportError:
    from .pieces import PieceType, get_piece_directions, KNIGHT_MOVES, KING_MOVES
    from .board import Board

class Game:
    """
    High-level game controller that manages game state and validates moves.
    """

    def __init__(self, white_player_id: str, black_player_id: str):
        self.board = Board()
        self.white_player_id = white_player_id
        self.black_player_id = black_player_id
        self.current_turn = 'white'
        self.move_history = []
        self.status = 'ongoing'  # ongoing, checkmate, stalemate, resignation, draw
        self.winner = None
        self.castling_rights = {
            'white': {'kingside': True, 'queenside': True},
            'black': {'kingside': True, 'queenside': True}
        }
        self.en_passant_target = None  # Square where en passant is possible
        self.halfmove_clock = 0  # Moves since last capture or pawn move (for 50-move rule)
        self.fullmove_number = 1

    def start_game(self):
        """Initialize board with random Chess 39 armies."""
        self.board.setup_board()

    def make_move(self, from_sq: str, to_sq: str, player_id: str, promotion_piece: Optional[PieceType] = None) -> dict:
        """
        Validate and execute a move.
        
        Args:
            from_sq: Starting square (e.g., 'e2')
            to_sq: Destination square (e.g., 'e4')
            player_id: ID of the player making the move
            promotion_piece: Piece type to promote to (if pawn reaches end rank)
            
        Returns:
            dict with 'success' bool and 'message' string
        """
        # Verify it's the player's turn
        if (self.current_turn == 'white' and player_id != self.white_player_id) or \
           (self.current_turn == 'black' and player_id != self.black_player_id):
            return {'success': False, 'message': 'Not your turn'}

        # Verify game is ongoing
        if self.status != 'ongoing':
            return {'success': False, 'message': f'Game is {self.status}'}

        # Get piece at from_sq
        piece_data = self.board.grid.get(from_sq)
        if not piece_data:
            return {'success': False, 'message': 'No piece at source square'}

        piece_type, piece_color = piece_data

        # Verify piece color matches current turn
        if piece_color != self.current_turn:
            return {'success': False, 'message': 'Cannot move opponent\'s piece'}

        # Validate the move
        if not self._is_valid_move(from_sq, to_sq, piece_type, piece_color):
            return {'success': False, 'message': 'Invalid move'}

        # Check if move would leave king in check
        if self._would_be_in_check_after_move(from_sq, to_sq, piece_color):
            return {'success': False, 'message': 'Move would leave king in check'}

        # Execute the move
        captured_piece = self._execute_move(from_sq, to_sq, piece_type, piece_color, promotion_piece)

        # Record move in history
        self.move_history.append({
            'from': from_sq,
            'to': to_sq,
            'piece': piece_type.name,
            'captured': captured_piece.name if captured_piece else None,
            'move_number': self.fullmove_number
        })

        # Switch turns
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        if self.current_turn == 'white':
            self.fullmove_number += 1

        # Check for game over conditions
        self._check_game_over()

        return {
            'success': True,
            'message': 'Move successful',
            'captured': captured_piece.name if captured_piece else None,
            'is_check': self.is_in_check(self.current_turn),
            'status': self.status
        }

    def _is_valid_move(self, from_sq: str, to_sq: str, piece_type: PieceType, piece_color: str) -> bool:
        """Check if a move is valid according to chess rules."""
        if from_sq == to_sq:
            return False

        # Get square coordinates
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        # Check if destination is off board
        if not (0 <= to_col < 8 and 0 <= to_row < 8):
            return False

        # Check if destination has same color piece
        dest_piece = self.board.grid.get(to_sq)
        if dest_piece and dest_piece[1] == piece_color:
            return False

        # Piece-specific move validation
        if piece_type == PieceType.PAWN:
            return self._is_valid_pawn_move(from_sq, to_sq, piece_color)
        elif piece_type == PieceType.KNIGHT:
            return self._is_valid_knight_move(from_sq, to_sq)
        elif piece_type == PieceType.BISHOP:
            return self._is_valid_bishop_move(from_sq, to_sq)
        elif piece_type == PieceType.ROOK:
            return self._is_valid_rook_move(from_sq, to_sq)
        elif piece_type == PieceType.QUEEN:
            return self._is_valid_queen_move(from_sq, to_sq)
        elif piece_type == PieceType.KING:
            return self._is_valid_king_move(from_sq, to_sq, piece_color)

        return False

    def _is_valid_pawn_move(self, from_sq: str, to_sq: str, color: str) -> bool:
        """Validate pawn moves (forward, double-forward, captures, en passant)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        direction = 1 if color == 'white' else -1
        start_row = 1 if color == 'white' else 6

        dest_piece = self.board.grid.get(to_sq)

        # Forward move (one square)
        if from_col == to_col and to_row == from_row + direction:
            return dest_piece is None

        # Double forward move (from starting position)
        if from_col == to_col and from_row == start_row and to_row == from_row + 2 * direction:
            middle_sq = self._coords_to_square(from_col, from_row + direction)
            return dest_piece is None and self.board.grid.get(middle_sq) is None

        # Diagonal capture
        if abs(to_col - from_col) == 1 and to_row == from_row + direction:
            # Normal capture
            if dest_piece and dest_piece[1] != color:
                return True
            # En passant
            if to_sq == self.en_passant_target:
                return True

        return False

    def _is_valid_knight_move(self, from_sq: str, to_sq: str) -> bool:
        """Validate knight moves (L-shape)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        diff_col = to_col - from_col
        diff_row = to_row - from_row

        return (diff_col, diff_row) in KNIGHT_MOVES

    def _is_valid_bishop_move(self, from_sq: str, to_sq: str) -> bool:
        """Validate bishop moves (diagonal)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        diff_col = abs(to_col - from_col)
        diff_row = abs(to_row - from_row)

        # Must move diagonally
        if diff_col != diff_row or diff_col == 0:
            return False

        # Check path is clear
        return self._is_path_clear(from_sq, to_sq)

    def _is_valid_rook_move(self, from_sq: str, to_sq: str) -> bool:
        """Validate rook moves (orthogonal)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        # Must move in straight line (same row or column)
        if from_col != to_col and from_row != to_row:
            return False

        # Check path is clear
        return self._is_path_clear(from_sq, to_sq)

    def _is_valid_queen_move(self, from_sq: str, to_sq: str) -> bool:
        """Validate queen moves (diagonal or orthogonal)."""
        return self._is_valid_bishop_move(from_sq, to_sq) or self._is_valid_rook_move(from_sq, to_sq)

    def _is_valid_king_move(self, from_sq: str, to_sq: str, color: str) -> bool:
        """Validate king moves (one square any direction + castling)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        diff_col = abs(to_col - from_col)
        diff_row = abs(to_row - from_row)

        # Normal king move (one square)
        if diff_col <= 1 and diff_row <= 1:
            return True

        # Castling (two squares horizontally)
        if diff_col == 2 and diff_row == 0:
            return self._can_castle(from_sq, to_sq, color)

        return False

    def _can_castle(self, from_sq: str, to_sq: str, color: str) -> bool:
        """Check if castling is legal."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        # Determine castling side
        if to_col > from_col:
            side = 'kingside'
            rook_col = 7
        else:
            side = 'queenside'
            rook_col = 0

        # Check castling rights
        if not self.castling_rights[color][side]:
            return False

        # Check king is not in check
        if self.is_in_check(color):
            return False

        # Check squares between king and rook are empty
        step = 1 if to_col > from_col else -1
        for col in range(from_col + step, rook_col, step):
            sq = self._coords_to_square(col, from_row)
            if self.board.grid.get(sq) is not None:
                return False

        # Check king doesn't pass through or land on attacked square
        for col in range(from_col, to_col + step, step):
            sq = self._coords_to_square(col, from_row)
            if self._is_square_attacked(sq, 'white' if color == 'black' else 'black'):
                return False

        return True

    def _is_path_clear(self, from_sq: str, to_sq: str) -> bool:
        """Check if path between two squares is clear (for sliding pieces)."""
        from_col, from_row = self._square_to_coords(from_sq)
        to_col, to_row = self._square_to_coords(to_sq)

        col_step = 0 if from_col == to_col else (1 if to_col > from_col else -1)
        row_step = 0 if from_row == to_row else (1 if to_row > from_row else -1)

        current_col, current_row = from_col + col_step, from_row + row_step

        while (current_col, current_row) != (to_col, to_row):
            sq = self._coords_to_square(current_col, current_row)
            if self.board.grid.get(sq) is not None:
                return False
            current_col += col_step
            current_row += row_step

        return True

    def _execute_move(self, from_sq: str, to_sq: str, piece_type: PieceType, 
                     piece_color: str, promotion_piece: Optional[PieceType]) -> Optional[PieceType]:
        """Execute a move on the board and handle special cases."""
        # Capture piece if present
        dest_piece = self.board.grid.get(to_sq)
        captured_piece = dest_piece[0] if dest_piece else None

        # Move the piece
        self.board.grid[to_sq] = (piece_type, piece_color)
        self.board.grid[from_sq] = None

        # Handle pawn promotion
        to_col, to_row = self._square_to_coords(to_sq)
        if piece_type == PieceType.PAWN:
            if (piece_color == 'white' and to_row == 7) or (piece_color == 'black' and to_row == 0):
                # Promote to queen by default if not specified
                promo = promotion_piece if promotion_piece else PieceType.QUEEN
                self.board.grid[to_sq] = (promo, piece_color)

        # Handle castling (move rook)
        if piece_type == PieceType.KING:
            from_col, from_row = self._square_to_coords(from_sq)
            diff_col = to_col - from_col
            if abs(diff_col) == 2:  # Castling occurred
                if diff_col > 0:  # Kingside
                    rook_from = self._coords_to_square(7, from_row)
                    rook_to = self._coords_to_square(5, from_row)
                else:  # Queenside
                    rook_from = self._coords_to_square(0, from_row)
                    rook_to = self._coords_to_square(3, from_row)
                
                rook_data = self.board.grid[rook_from]
                self.board.grid[rook_to] = rook_data
                self.board.grid[rook_from] = None

        # Update castling rights
        if piece_type == PieceType.KING:
            self.castling_rights[piece_color]['kingside'] = False
            self.castling_rights[piece_color]['queenside'] = False
        elif piece_type == PieceType.ROOK:
            from_col, from_row = self._square_to_coords(from_sq)
            if from_col == 0:
                self.castling_rights[piece_color]['queenside'] = False
            elif from_col == 7:
                self.castling_rights[piece_color]['kingside'] = False

        # Update en passant target
        from_col, from_row = self._square_to_coords(from_sq)
        if piece_type == PieceType.PAWN and abs(to_row - from_row) == 2:
            ep_row = (from_row + to_row) // 2
            self.en_passant_target = self._coords_to_square(from_col, ep_row)
        else:
            self.en_passant_target = None

        # Update halfmove clock
        if piece_type == PieceType.PAWN or captured_piece:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        return captured_piece

    def is_in_check(self, color: str) -> bool:
        """Check if the king of the given color is in check."""
        # Find king position
        king_square = None
        for square, piece_data in self.board.grid.items():
            if piece_data and piece_data[0] == PieceType.KING and piece_data[1] == color:
                king_square = square
                break

        if not king_square:
            return False  # No king found (shouldn't happen in valid game)

        # Check if king square is attacked by opponent
        opponent_color = 'black' if color == 'white' else 'white'
        return self._is_square_attacked(king_square, opponent_color)

    def _is_square_attacked(self, square: str, by_color: str) -> bool:
        """Check if a square is attacked by pieces of the given color."""
        for from_sq, piece_data in self.board.grid.items():
            if piece_data and piece_data[1] == by_color:
                piece_type = piece_data[0]
                # Check if this piece can attack the square
                if self._is_valid_move(from_sq, square, piece_type, by_color):
                    return True
        return False

    def _would_be_in_check_after_move(self, from_sq: str, to_sq: str, color: str) -> bool:
        """Test if a move would leave the player's king in check."""
        # Save current state
        from_piece = self.board.grid[from_sq]
        to_piece = self.board.grid.get(to_sq)

        # Make temporary move
        self.board.grid[to_sq] = from_piece
        self.board.grid[from_sq] = None

        # Check if in check
        in_check = self.is_in_check(color)

        # Restore state
        self.board.grid[from_sq] = from_piece
        self.board.grid[to_sq] = to_piece

        return in_check

    def _check_game_over(self):
        """Check for checkmate, stalemate, or draw conditions."""
        current_color = self.current_turn

        # Get all legal moves for current player
        has_legal_move = False
        for from_sq, piece_data in self.board.grid.items():
            if piece_data and piece_data[1] == current_color:
                piece_type = piece_data[0]
                for to_sq in self.board.grid.keys():
                    if self._is_valid_move(from_sq, to_sq, piece_type, current_color):
                        if not self._would_be_in_check_after_move(from_sq, to_sq, current_color):
                            has_legal_move = True
                            break
            if has_legal_move:
                break

        if not has_legal_move:
            if self.is_in_check(current_color):
                # Checkmate
                self.status = 'checkmate'
                self.winner = 'black' if current_color == 'white' else 'white'
            else:
                # Stalemate
                self.status = 'stalemate'

        # Check for 50-move rule
        if self.halfmove_clock >= 100:  # 50 moves per player
            self.status = 'draw'

    def resign(self, player_id: str) -> dict:
        """Handle player resignation."""
        if self.status != 'ongoing':
            return {'success': False, 'message': 'Game is not ongoing'}

        self.status = 'resignation'
        if player_id == self.white_player_id:
            self.winner = 'black'
        else:
            self.winner = 'white'

        return {'success': True, 'message': 'Resignation accepted', 'winner': self.winner}

    def get_state(self) -> dict:
        """Serialize complete game state to JSON-compatible dict."""
        return {
            'white_player_id': self.white_player_id,
            'black_player_id': self.black_player_id,
            'current_turn': self.current_turn,
            'board': {sq: (p[0].name, p[1]) if p else None for sq, p in self.board.grid.items()},
            'move_history': self.move_history,
            'status': self.status,
            'winner': self.winner,
            'castling_rights': self.castling_rights,
            'en_passant_target': self.en_passant_target,
            'halfmove_clock': self.halfmove_clock,
            'fullmove_number': self.fullmove_number
        }

    @staticmethod
    def from_state(state: dict) -> 'Game':
        """Deserialize game from JSON state dict."""
        game = Game(state['white_player_id'], state['black_player_id'])
        game.current_turn = state['current_turn']
        game.move_history = state['move_history']
        game.status = state['status']
        game.winner = state['winner']
        game.castling_rights = state['castling_rights']
        game.en_passant_target = state['en_passant_target']
        game.halfmove_clock = state['halfmove_clock']
        game.fullmove_number = state['fullmove_number']

        # Reconstruct board
        for square, piece_data in state['board'].items():
            if piece_data:
                piece_type = PieceType[piece_data[0]]
                color = piece_data[1]
                game.board.grid[square] = (piece_type, color)
            else:
                game.board.grid[square] = None

        return game

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        """Convert square notation (e.g., 'e4') to coordinates (4, 3)."""
        col = ord(square[0]) - ord('a')
        row = int(square[1]) - 1
        return col, row

    def _coords_to_square(self, col: int, row: int) -> str:
        """Convert coordinates (4, 3) to square notation ('e4')."""
        return chr(col + ord('a')) + str(row + 1)
