"""
FEN (Forsyth-Edwards Notation) support for Chess 39.

Provides functionality to convert board states to/from FEN notation
to enable game state persistence andreplay.
"""

from typing import Dict, Tuple
from .pieces import PieceType


PIECE_TO_FEN = {
    PieceType.PAWN: 'p',
    PieceType.KNIGHT: 'n',
    PieceType.BISHOP: 'b',
    PieceType.ROOK: 'r',
    PieceType.QUEEN: 'q',
    PieceType.KING: 'k',
}

FEN_TO_PIECE = {v: k for k, v in PIECE_TO_FEN.items()}


def board_to_fen(grid: Dict, current_turn: str, castling_rights: Dict, 
                 en_passant_target: str, halfmove_clock: int, fullmove_number: int) -> str:
    """
    Convert a Chess 39 board state to FEN notation.
    
    Args:
        grid: Board grid dictionary
        current_turn: 'white' or 'black'
        castling_rights: Dict with castling availability
        en_passant_target: Square where en passant is possible (or None)
        halfmove_clock: Halfmove clock for 50-move rule
        fullmove_number: Full move number
        
    Returns:
        FEN string representing the position
    """
    # 1. Piece placement
    fen_rows = []
    for row in range(7, -1, -1):  # Start from rank 8
        fen_row = ""
        empty_count = 0
        
        for col in range(8):
            square = chr(ord('a') + col) + str(row + 1)
            piece_data = grid.get(square)
            
            if piece_data is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                
                piece_type, color = piece_data
                piece_char = PIECE_TO_FEN[piece_type]
                if color == 'white':
                    piece_char = piece_char.upper()
                fen_row += piece_char
        
        if empty_count > 0:
            fen_row += str(empty_count)
        
        fen_rows.append(fen_row)
    
    position = '/'.join(fen_rows)
    
    # 2. Active color
    active_color = 'w' if current_turn == 'white' else 'b'
    
    # 3. Castling availability
    castling = ''
    if castling_rights['white']['kingside']:
        castling += 'K'
    if castling_rights['white']['queenside']:
        castling += 'Q'
    if castling_rights['black']['kingside']:
        castling += 'k'
    if castling_rights['black']['queenside']:
        castling += 'q'
    if not castling:
        castling = '-'
    
    # 4. En passant target square
    en_passant = en_passant_target if en_passant_target else '-'
    
    # 5. Halfmove clock
    halfmove = str(halfmove_clock)
    
    # 6. Fullmove number
    fullmove = str(fullmove_number)
    
    return f"{position} {active_color} {castling} {en_passant} {halfmove} {fullmove}"


def fen_to_board(fen: str) -> Tuple[Dict, str, Dict, str, int, int]:
    """
    Parse a FEN string and return board state components.
    
    Returns:
        Tuple of (grid, current_turn, castling_rights, en_passant_target, halfmove_clock, fullmove_number)
    """
    parts = fen.split()
    
    # 1. Parse piece placement
    grid = {f"{chr(ord('a') + col)}{row + 1}": None for col in range(8) for row in range(8)}
    
    rows = parts[0].split('/')
    for row_idx, row_fen in enumerate(rows):
        row = 7 - row_idx  # FEN starts from rank 8
        col = 0
        
        for char in row_fen:
            if char.isdigit():
                col += int(char)
            else:
                piece_char = char.lower()
                piece_type = FEN_TO_PIECE.get(piece_char)
                color = 'white' if char.isupper() else 'black'
                
                square = chr(ord('a') + col) + str(row + 1)
                grid[square] = (piece_type, color)
                col += 1
    
    # 2. Active color
    current_turn = 'white' if parts[1] == 'w' else 'black'
    
    # 3. Castling availability
    castling_rights = {
        'white': {'kingside': False, 'queenside': False},
        'black': {'kingside': False, 'queenside': False}
    }
    if 'K' in parts[2]:
        castling_rights['white']['kingside'] = True
    if 'Q' in parts[2]:
        castling_rights['white']['queenside'] = True
    if 'k' in parts[2]:
        castling_rights['black']['kingside'] = True
    if 'q' in parts[2]:
        castling_rights['black']['queenside'] = True
    
    # 4. En passant target
    en_passant_target = parts[3] if parts[3] != '-' else None
    
    # 5. Halfmove clock
    halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
    
    # 6. Fullmove number
    fullmove_number = int(parts[5]) if len(parts) > 5 else 1
    
    return grid, current_turn, castling_rights, en_passant_target, halfmove_clock, fullmove_number
