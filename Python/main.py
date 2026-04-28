import engine
import math
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIN_SCORE  =  1_000_000
LOSS_SCORE = -1_000_000
MAX_DEPTH  = 10
TIME_LIMIT = 4.0

# Pre-computed move priority lookup (avoids set creation on every call)
_MOVE_PRIORITY = [
    2 if (i % 9) in {1, 3, 5, 7} else (0 if (i % 9) == 4 else 1)
    for i in range(81)
]

def order_moves(moves):
    return sorted(moves, key=_MOVE_PRIORITY.__getitem__)


# ---------------------------------------------------------------------------
# Transposition table
# Stores: (depth, flag, value)
# flag: 0 = exact, 1 = lower bound (beta cut), 2 = upper bound (alpha cut)
# ---------------------------------------------------------------------------
_tt: dict = {}

# Flag constants (faster than string comparison)
_EXACT = 0
_LOWER = 1
_UPPER = 2


def minimax(game, depth, alpha, beta, maximizing):
    # --- Terminal / leaf ---
    if game.is_done():
        w = game.get_winner()
        if w == 1:   return WIN_SCORE
        if w == -1:  return LOSS_SCORE
        return 0

    if depth == 0:
        raw = game.eval() * 900_000
        return raw if maximizing else -raw

    moves = game.get_legal_moves()
    if not moves:
        return 0

    # --- Transposition table lookup ---
    # Use id of a hashable state representation; get_state() must return something hashable.
    state_key = (game.get_hash(), maximizing)
    tt_entry = _tt.get(state_key)
    if tt_entry is not None:
        cached_depth, flag, cached_val = tt_entry
        if cached_depth >= depth:
            if flag == _EXACT:
                return cached_val
            elif flag == _LOWER:
                if cached_val > alpha:
                    alpha = cached_val
            else:  # _UPPER
                if cached_val < beta:
                    beta = cached_val
            if alpha >= beta:
                return cached_val

    moves = order_moves(moves)
    original_alpha = alpha

    if maximizing:
        value = -math.inf
        for m in moves:
            game.apply_move(m)
            child = minimax(game, depth - 1, alpha, beta, False)
            game.undo()
            if child > value:
                value = child
                if value > alpha:
                    alpha = value
                    if alpha >= beta:
                        break
    else:
        value = math.inf
        for m in moves:
            game.apply_move(m)
            child = minimax(game, depth - 1, alpha, beta, True)
            game.undo()
            if child < value:
                value = child
                if value < beta:
                    beta = value
                    if beta <= alpha:
                        break

    # --- Store in TT ---
    if value <= original_alpha:
        flag = _UPPER
    elif value >= beta:
        flag = _LOWER
    else:
        flag = _EXACT
    _tt[state_key] = (depth, flag, value)

    return value


def best_move(game, max_depth=MAX_DEPTH, time_limit=TIME_LIMIT):
    moves = game.get_legal_moves()
    assert moves, "best_move called with no legal moves"

    moves = order_moves(moves)
    chosen = moves[0]
    start  = time.monotonic()

    state = game.get_state()
    maximizing_root = (state[90] == 1)

    # Aspiration window parameters
    ASPIRATION_DELTA = 50_000

    prev_score = 0  # seed for aspiration windows

    for depth in range(1, max_depth + 1):
        if time.monotonic() - start > time_limit:
            break

        # --- Aspiration windows (skip for depth 1 to get a reliable seed) ---
        if depth > 1:
            alpha = prev_score - ASPIRATION_DELTA
            beta  = prev_score + ASPIRATION_DELTA
        else:
            alpha = -math.inf
            beta  =  math.inf

        best_val   = -math.inf
        depth_best = chosen
        timeout    = False

        # Re-sort moves using previous best move first (PV move ordering)
        if depth > 1 and chosen in moves:
            moves.remove(chosen)
            moves.insert(0, chosen)

        while True:   # aspiration re-search loop
            best_val   = -math.inf
            depth_best = chosen

            for m in moves:
                if time.monotonic() - start > time_limit:
                    timeout = True
                    break
                game.apply_move(m)
                val = minimax(game, depth - 1, alpha, beta, not maximizing_root)
                game.undo()

                if val > best_val:
                    best_val   = val
                    depth_best = m
                if val > alpha:
                    alpha = val

            if timeout:
                break

            # Check if result fell outside aspiration window → re-search
            if depth > 1 and best_val <= prev_score - ASPIRATION_DELTA:
                # Failed low: open lower bound
                alpha = -math.inf
                beta  = best_val + 1
            elif depth > 1 and best_val >= prev_score + ASPIRATION_DELTA:
                # Failed high: open upper bound
                alpha = best_val - 1
                beta  = math.inf
            else:
                break   # result is inside window, accept it

        if not timeout:
            chosen     = depth_best
            prev_score = best_val

        elapsed  = time.monotonic() - start
        tt_size  = len(_tt)
        print(f"  [depth={depth}] move={chosen}  score={best_val:.1f}"
              f"  ({elapsed:.2f}s)  TT={tt_size}")

        if best_val >= WIN_SCORE:
            break

    return chosen


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------
def coord_to_move(col, row):
    """(col, row) 1-indexed on a 9×9 grid → move index 0–80."""
    col -= 1;  row -= 1
    board_col = col // 3;  board_row = row // 3
    cell_col  = col % 3;   cell_row  = row % 3
    return (board_row * 3 + board_col) * 9 + cell_row * 3 + cell_col


def move_to_coord(move):
    """Move index 0–80 → (col, row) 1-indexed."""
    board_index = move // 9;  cell_index = move % 9
    board_col = board_index % 3;  board_row = board_index // 3
    cell_col  = cell_index  % 3;  cell_row  = cell_index  // 3
    return board_col * 3 + cell_col + 1, board_row * 3 + cell_row + 1


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
def play_game(human_starts=True):
    global _tt
    _tt = {}

    game        = engine.Game()
    move_number = 0

    print("\n=== Ultimate Tic Tac Toe — Minimax Alpha-Beta ===")
    print(f"  Human {'goes first (player 1 / X)' if human_starts else 'is player 2 / O'}")

    human_turn = human_starts

    while not game.is_done():
        move_number += 1
        legal = game.get_legal_moves()

        print("\nCurrent board:")
        game.print_board()
        print(f"\n--- Move {move_number} | {'Human' if human_turn else 'AI'} ---")

        if human_turn:
            while True:
                try:
                    c = int(input("col: "))
                    l = int(input("row: "))
                    m = coord_to_move(c, l)
                    if m in legal:
                        break
                    print("  Illegal move.")
                except ValueError:
                    print("  Please enter an integer.")
            game.apply_move(m)
            print(f"  → Human plays {m}")

        else:
            t0 = time.monotonic()
            m  = best_move(game)
            game.apply_move(m)
            print(f"  → AI plays {move_to_coord(m)}  ({time.monotonic() - t0:.2f}s)")

        print("\nBoard after move:")
        game.print_board()
        human_turn = not human_turn

    print("\nFinal board:")
    game.print_board()

    w = game.get_winner()
    print("\n=== Game over ===")
    if w == 0:
        print("Draw!")
    elif (w == 1 and human_starts) or (w == -1 and not human_starts):
        print("Human wins!")
    else:
        print("AI wins!")
def play_AIgame():
    global _tt
    _tt = {}

    game        = engine.Game()
    move_number = 0

    print("\n=== Ultimate Tic Tac Toe — Minimax Alpha-Beta ===")
    human_turn=True

    while not game.is_done():
        move_number += 1
        legal = game.get_legal_moves()

        print("\nCurrent board:")
        game.print_board()
        print(f"\n--- Move {move_number} | {'1' if human_turn else '2'} ---")

        
        t0 = time.monotonic()
        m  = best_move(game)
        game.apply_move(m)
        print(f"  → AI plays {move_to_coord(m)}  ({time.monotonic() - t0:.2f}s)")

        print("\nBoard after move:")
        game.print_board()
        human_turn = not human_turn

    w = game.get_winner()
    print("\n=== Game over ===")
    if w == 0:
        print("Draw!")
    else:
        print(w,"wins")

if __name__ == "__main__":
    choice = input("Who goes first? [h]uman / [a]i: ").strip().lower()
    if(choice == "n"):
        play_AIgame()
    play_game(human_starts=(choice != "a"))