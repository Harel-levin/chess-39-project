import random
from .pieces import PieceType

# --- Configuration from our project plan ---
TARGET_POINTS = 39  # 
MAX_PAWNS = 8       # Implied by 

# List of "major" pieces we can pick from.
# We exclude PAWN (handled last) and KING (not counted in points [cite: 65]).
MAJOR_PIECES = [
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT
]

def generate_random_army():
    """
    Generates a random list of PieceType members that
    sum exactly to TARGET_POINTS, respecting constraints.

    This logic uses the "Top-Down, Fill & Retry" strategy.
    It picks major pieces randomly, then fills the remainder
    with pawns. If the pawn count is invalid, it retries.
    """

    # We start an infinite loop that we will 'break' out of
    # once we have a valid army.
    while True:
        army = []
        remaining_points = TARGET_POINTS

        # We shuffle the list so we don't always
        # pick Queens first. This gives more random armies.
        random.shuffle(MAJOR_PIECES)

        for piece in MAJOR_PIECES:
            # How many *could* we add?
            # e.g., 39 remaining // 9 (Queen) = 4 max
            max_possible = remaining_points // piece.value

            # How many *will* we add? (from 0 to max_possible)
            num_to_add = random.randint(0, max_possible)

            # Add them to the army
            army.extend([piece] * num_to_add)

            # Update our remaining "budget"
            remaining_points -= num_to_add * piece.value

        # At this point, `remaining_points` MUST be filled by pawns,
        # since PAWN.value is 1.
        num_pawns = remaining_points

        # --- Validation Step ---
        # Did we need too many pawns?
        if num_pawns <= MAX_PAWNS:
            # No, this is a valid army!
            army.extend([PieceType.PAWN] * num_pawns)

            # Break the 'while True' loop, we are done!
            break
        else:
            # Yes, we needed (e.g.) 10 pawns. This is invalid.
            # The 'while True' loop will simply run again
            # from the top, trying a new random combination.
            pass

    # Finally, don't forget the King!
    # The plan says the King is *always* present but
    # not counted in the 39 points[cite: 55, 65].
    army.append(PieceType.KING)

    return army

# --- Test Block ---
# This code only runs when you run this file directly
if __name__ == "__main__":
    print("--- Testing our Chess 39 Army Generator ---")

    for i in range(5): # Generate 5 test armies
        print(f"\n--- Test Army {i+1} ---")
        new_army = generate_random_army()

        total_value = 0
        piece_counts = {}

        print(f"Generated Army (pieces): {[piece.name for piece in new_army]}")

        for piece in new_army:
            total_value += piece.value

            # Count the pieces for our summary
            piece_counts[piece.name] = piece_counts.get(piece.name, 0) + 1

        print(f"Generated Army (counts): {piece_counts}")
        print(f"Total Value: {total_value} points")

        # Check our work
        if total_value == TARGET_POINTS:
            print("Validation: PASS (39 points)")
        else:
            print(f"Validation: FAIL (Expected 39, got {total_value})")

        num_pawns = piece_counts.get("PAWN", 0)
        if num_pawns <= MAX_PAWNS:
            print(f"Validation: PASS ({num_pawns} pawns <= {MAX_PAWNS})")
        else:
            print(f"Validation: FAIL ({num_pawns} pawns > {MAX_PAWNS})")