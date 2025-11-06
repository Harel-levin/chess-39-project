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

# run this code if the file is run directly
if __name__ == "__main__":
    print("--- Testing our Chess 39 Piece Definitions ---")

    # You can access the name and value of each piece
    print(f"Piece: {PieceType.QUEEN.name}, Value: {PieceType.QUEEN.value} points")
    print(f"Piece: {PieceType.PAWN.name}, Value: {PieceType.PAWN.value} point")

    # Let's list all of them
    print("\nAll Pieces:")
    for piece in PieceType:
        print(f"  - {piece.name:6} (Value: {piece.value})")