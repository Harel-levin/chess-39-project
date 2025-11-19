import enum

class PieceType(enum.Enum):
    """
    Represents the different types of pieces in Chess 39.
    Each piece is an "enumeration" member.

    We assign the point value from the project plan 
    as the value for each member.
    """

    # Piece values from the plan 
    PAWN = 1
    KNIGHT = 3
    BISHOP = 3
    ROOK = 5
    QUEEN = 9

    # The King is special. its value is not
    # counted toward the 39 points.
    # We give it a value of 0 here to represent that.
    KING = 0


# Movement patterns for each piece type
# Knights: exact offsets (L-shape moves)
KNIGHT_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]

# King: one square in any direction
KING_MOVES = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1)
]

# Directions for sliding pieces
ROOK_DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Orthogonal
BISHOP_DIRECTIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # Diagonal
QUEEN_DIRECTIONS = ROOK_DIRECTIONS + BISHOP_DIRECTIONS  # Both


def get_piece_directions(piece_type: PieceType):
    """
    Returns the movement directions for a given piece type.
    For sliding pieces (rook, bishop, queen), returns direction vectors.
    For jumping pieces (knight, king), returns exact offsets.
    For pawns, use special pawn movement logic.
    """
    if piece_type == PieceType.KNIGHT:
        return KNIGHT_MOVES
    elif piece_type == PieceType.KING:
        return KING_MOVES
    elif piece_type == PieceType.ROOK:
        return ROOK_DIRECTIONS
    elif piece_type == PieceType.BISHOP:
        return BISHOP_DIRECTIONS
    elif piece_type == PieceType.QUEEN:
        return QUEEN_DIRECTIONS
    elif piece_type == PieceType.PAWN:
        return None  # Pawns have special movement logic
    return []


# Simple test code to display all pieces and their values
if __name__ == "__main__":
    print("\nAll Pieces:")
    for piece in PieceType:
        print(f"  - {piece.name:6} (Value: {piece.value})")