import random

from .pieces import PieceType
from .army import generate_random_army

PIECE_SYMBOLS = {
    PieceType.PAWN: "P",
    PieceType.KNIGHT: "N",
    PieceType.BISHOP: "B",
    PieceType.ROOK: "R",
    PieceType.QUEEN: "Q",
    PieceType.KING: "K",
}

class Board:
    """
        Represents the Chess 39 board and game state.
    """

    def __init__(self):
        self.grid = self._create_empty_grid()

    def _create_empty_grid(self):
        """
            A helper method to generate our dictionary of 64 squares.
        """
        grid = {}
        cols = 'abcdefgh'
        rows = '12345678'

        for col in cols:
            for row in rows:
                square_name = f"{col}{row}"
                grid[square_name] = None  # No piece on the square initially

        return grid

    def setup_board(self):
        """
            Sets up the board with a random army for each side.
        """
        white_army = generate_random_army()
        self.place_army(white_army, is_white=True)
        black_army = generate_random_army()
        self.place_army(black_army, is_white=False)

    def place_army(self, army, is_white):


        """
            Places the given army on the board for the specified color.
        """
        # Determine which ranks to use based on color
        rank_1 = "1" if is_white else "8" # Back rank
        rank_2 = "2" if is_white else "7" # Pawn rank

        rank_1_squares = [f"{col}{rank_1}" for col in 'abcdefgh']
        rank_2_squares = [f"{col}{rank_2}" for col in 'abcdefgh']

        king = army.pop(army.index(PieceType.KING))
        king_square = random.choice(rank_1_squares)

        self.grid[king_square] = (king, 'W' if is_white else 'B')
        rank_1_squares.remove(king_square)

        army.sort(key=lambda piece: piece == PieceType.PAWN, reverse=True)

        for piece in army:
            if piece == PieceType.PAWN:
                if rank_2_squares: # Make sure there is space
                    pawn_square = rank_2_squares.pop(0) # "left-to-right"
                    self.grid[pawn_square] = (piece, "white" if is_white else "black")
            else:
                    # 3. Place remaining pieces (Rule [cite: 70])
                if rank_1_squares: # Make sure there is space
                    piece_square = rank_1_squares.pop(0)
                    self.grid[piece_square] = (piece, "white" if is_white else "black")
        
        def print_board(self):
            """
            Displays the current board state in the terminal.
            This is our "visualizer" so we can see our work.
            """
            print("\n--- Chess 39 Board ---")
            # We loop from 8 *down to* 1
            for row in "87654321":
                row_str = f"{row} | "
                for col in "abcdefgh":
                    square = f"{col}{row}"
                    piece_data = self.grid[square] # This will be None or (PieceType, "color")

                    if piece_data is None:
                        row_str += ". "
                    else:
                        piece_type, color = piece_data
                        symbol = PIECE_SYMBOLS[piece_type]
                        # Show white as uppercase, black as lowercase
                        row_str += f"{symbol.upper() if color == 'white' else symbol.lower()} "

                print(row_str)

            print("   -----------------")
            print("    a b c d e f g h")

    def print_board(self):
        """
        Displays the current board state in the terminal.
        This is our "visualizer" so we can see our work.
        """
        print("\n--- Chess 39 Board ---")
        # We loop from 8 *down to* 1
        for row in "87654321":
            row_str = f"{row} | "
            for col in "abcdefgh":
                square = f"{col}{row}"
                piece_data = self.grid[square] # This will be None or (PieceType, "color")

                if piece_data is None:
                    row_str += ". "
                else:
                    piece_type, color = piece_data
                    symbol = PIECE_SYMBOLS[piece_type]
                    # Show white as uppercase, black as lowercase
                    row_str += f"{symbol.upper() if color == 'white' else symbol.lower()} "

            print(row_str)

        print("   -----------------")
        print("    a b c d e f g h")

# --- Test Block ---

if __name__ == "__main__":
    print("--- Testing our Chess 39 Board Setup ---")
    board = Board()
    board.setup_board()
    board.print_board()

    print("\n--- Testing the Grid (Dictionary) ---")
    print(f"Piece at e1: {board.grid['e1']}")
    print(f"Piece at d7: {board.grid['d7']}")
    print(f"Piece at a4 ()): {board.grid['a4']}")
            

