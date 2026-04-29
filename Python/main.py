import engine
import math
import time
import random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIN_SCORE      =  1_000_000
LOSS_SCORE     = -1_000_000
CONFIRMED_WIN  =    999_000   # only reached via is_done() terminal, not eval()
MAX_DEPTH      = 100
TIME_LIMIT     = 0.1

# ---------------------------------------------------------------------------
# Move ordering
#
# In Ultimate TTT, within each sub-board:
#   cell 4 (centre) is best
#   cells 0,2,6,8 (corners) are next
#   cells 1,3,5,7 (edges) are worst
#
# Priority value: LOWER number = searched FIRST.
# ---------------------------------------------------------------------------
_CELL_PRIORITY = [
    1,   # 0 corner
    2,   # 1 edge   (worst)
    1,   # 2 corner
    2,   # 3 edge
    0,   # 4 centre (best)
    2,   # 5 edge
    1,   # 6 corner
    2,   # 7 edge
    1,   # 8 corner
]

_MOVE_PRIORITY = [_CELL_PRIORITY[i % 9] for i in range(81)]


def order_moves(moves, pv_move=None):
    """Sort: PV move first, then centre, corners, edges."""
    if pv_move is not None and pv_move in moves:
        rest = sorted((m for m in moves if m != pv_move), key=lambda m: _MOVE_PRIORITY[m])
        return [pv_move] + rest
    return sorted(moves, key=lambda m: _MOVE_PRIORITY[m])


# ---------------------------------------------------------------------------
# Transposition table
# ---------------------------------------------------------------------------
_tt: dict = {}
_EXACT = 0
_LOWER = 1   # fail-high / lower bound
_UPPER = 2   # fail-low  / upper bound


def _eval_for_mover(game):
    """game.eval() is from X's perspective. Flip for O."""
    raw = game.eval()
    return raw if game.get_current_player() == 1 else -raw


def minimax(game, depth, alpha, beta):
    """Negamax alpha-beta. Score from mover's perspective."""
    if game.is_done():
        w = game.get_winner()
        if w == 0:
            return 0
        # In negamax: the player about to move has already lost.
        # The winner was the one who just moved (not current player).
        return LOSS_SCORE  # always from mover's POV

    if depth == 0:
        return _eval_for_mover(game)
    
    moves = game.get_legal_moves()
    if not moves:
        return 0

    # TT probe
    key      = game.get_hash()
    tt_entry = _tt.get(key)
    if tt_entry is not None:
        cached_depth, flag, cached_val = tt_entry
        if cached_depth >= depth:
            if flag == _EXACT:
                return cached_val
            elif flag == _LOWER and cached_val > alpha:
                alpha = cached_val
            elif flag == _UPPER and cached_val < beta:
                beta = cached_val
            if alpha >= beta:
                return cached_val

    original_alpha = alpha
    value          = -math.inf

    for m in order_moves(moves):
        game.apply_move(m)
        child = -minimax(game, depth - 1, -beta, -alpha)
        game.undo()
        if child > value:
            value = child
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    # TT store
    if value <= original_alpha:
        flag = _UPPER
    elif value >= beta:
        flag = _LOWER
    else:
        flag = _EXACT
    _tt[key] = (depth, flag, value)

    return value


# ---------------------------------------------------------------------------
# Iterative deepening with aspiration windows
# ---------------------------------------------------------------------------
def best_move(game, max_depth=MAX_DEPTH, time_limit=TIME_LIMIT):
    global _tt

    moves = game.get_legal_moves()
    assert moves, "best_move called with no legal moves"

    if len(_tt) > 2_000_000:
        _tt = {}

    chosen     = order_moves(moves)[0]
    start      = time.monotonic()
    prev_score = 0
    DELTA      = 30_000

    for depth in range(1, max_depth + 1):
        if time.monotonic() - start >= time_limit:
            break

        alpha = (-math.inf if depth == 1 else prev_score - DELTA)
        beta  = ( math.inf if depth == 1 else prev_score + DELTA)

        while True:   # aspiration re-search loop
            best_val    = -math.inf
            depth_best  = chosen
            timeout     = False
            local_alpha = alpha

            for m in order_moves(moves, pv_move=chosen):
                if time.monotonic() - start >= time_limit:
                    timeout = True
                    break

                game.apply_move(m)
                val = -minimax(game, depth - 1, -beta, -local_alpha)
                game.undo()

                if val > best_val:
                    best_val  = val
                    depth_best = m
                if val > local_alpha:
                    local_alpha = val

            if timeout:
                break

            if depth == 1:
                break   # no aspiration on depth 1

            if best_val <= alpha:
                # Fail low: widen window downward
                DELTA *= 2
                alpha  = max(prev_score - DELTA, -math.inf)
                beta   = math.inf
            elif best_val >= beta:
                # Fail high: widen window upward
                DELTA *= 2
                alpha  = -math.inf
                beta   = min(prev_score + DELTA, math.inf)
            else:
                break   # within window, accept

        if not timeout:
            chosen     = depth_best
            prev_score = best_val
            DELTA      = 30_000   # reset for next depth

        # Only stop early if the score comes from a proven terminal node,
        # not just a high static eval. CONFIRMED_WIN is above any eval()
        # output but below WIN_SCORE, so only actual is_done() returns
        # can push past it.
        if abs(prev_score) >= CONFIRMED_WIN:
            break

    return chosen


# ---------------------------------------------------------------------------
# Training helper
# ---------------------------------------------------------------------------
def best_move_train(game):
    global _tt
    _tt = {}

    moves    = order_moves(game.get_legal_moves())
    best_val = -math.inf
    chosen   = moves[0]

    for m in moves:
        game.apply_move(m)
        val = -minimax(game, depth=2, alpha=-math.inf, beta=math.inf)
        game.undo()
        if val > best_val:
            best_val = val
            chosen   = m

    return chosen


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------
def coord_to_move(col, row):
    col -= 1; row -= 1
    board_col = col // 3; board_row = row // 3
    cell_col  = col % 3;  cell_row  = row % 3
    return (board_row * 3 + board_col) * 9 + cell_row * 3 + cell_col


def move_to_coord(move):
    board_index = move // 9; cell_index = move % 9
    board_col = board_index % 3; board_row = board_index // 3
    cell_col  = cell_index  % 3; cell_row  = cell_index  // 3
    return board_col * 3 + cell_col + 1, board_row * 3 + cell_row + 1


# ---------------------------------------------------------------------------
# Game loops
# ---------------------------------------------------------------------------
def play_game(human_starts=True):
    game       = engine.Game()
    move_number = 0
    human_turn  = human_starts

    print("\n=== Ultimate Tic Tac Toe ===")
    print(f"  Human {'goes first (X)' if human_starts else 'is O'}")

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
        else:
            t0 = time.monotonic()
            m  = best_move(game)
            game.apply_move(m)
            print(f"  → AI plays {move_to_coord(m)}  ({time.monotonic() - t0:.3f}s)")
            print(game.eval())

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


def play_AIgame(human_starts=False):
    global _tt
    _tt = {}
    game        = engine.Game()
    move_number = 0
    human_turn  = human_starts

    while not game.is_done():
        move_number += 1
        legal = game.get_legal_moves()
        if human_turn:
            game.apply_move(random.choice(legal))
        
        else:
            game.apply_move(best_move(game))
        
        print(game.eval())
        game.print_board()
        human_turn = not human_turn

    w = game.get_winner()
    if w == 0: print("Draw!")
    elif (w == 1 and human_starts) or (w == -1 and not human_starts): print("Random wins!")
    else: print("AI wins!")


def BenchmarkModel(n=20, ai_goes_first=False):
    """
    AI vs random for n games.
    ai_goes_first=False → AI is O (wins when get_winner()==-1)
    ai_goes_first=True  → AI is X (wins when get_winner()==1)
    """
    global _tt
    wins = draws = losses = 0
    ai_win_value = 1 if ai_goes_first else -1

    for i in range(n):
        _tt = {}
        game    = engine.Game()
        ai_turn = ai_goes_first

        while not game.is_done():
            legal = game.get_legal_moves()
            m = best_move(game) if ai_turn else random.choice(legal)
            game.apply_move(m)
            ai_turn = not ai_turn

        w = game.get_winner()
        if w == ai_win_value:
            wins += 1
        elif w == 0:
            draws += 1
        else:
            losses += 1
        print(f"game {i:2d}  {'WIN ' if w==ai_win_value else ('DRAW' if w==0 else 'LOSS')}"
              f"  running: {wins}W {draws}D {losses}L")

    print(f"\nFinal: {wins}W / {draws}D / {losses}L  ({100*wins//n}% win rate)")


if __name__ == "__main__":
    choice = input("Mode? [h]uman vs AI / [b]enchmark: ").strip().lower()
    if choice == "b":
        BenchmarkModel(n=20)
    elif choice =="n":
        play_AIgame()
    else:
        side = input("Who goes first? [h]uman / [a]i: ").strip().lower()
        play_game(human_starts=(side != "a"))