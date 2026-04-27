import engine
import math
import time

# Constantes
WIN_SCORE  =  1_000_000
LOSS_SCORE = -1_000_000
MAX_DEPTH  = 6
TIME_LIMIT = 4.0


def order_moves(moves):
    CENTER_CELLS = {4}
    CORNER_CELLS = {0, 2, 6, 8}

    def priority(m):
        local = m % 9
        if local in CENTER_CELLS: return 0
        if local in CORNER_CELLS: return 1
        return 2

    return sorted(moves, key=priority)


def minimax(game, depth, alpha, beta, maximizing):
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

    moves = order_moves(moves)

    if maximizing:
        value = -math.inf
        for m in moves:
            game.apply_move(m)
            value = max(value, minimax(game, depth - 1, alpha, beta, False))
            game.undo()
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = math.inf
        for m in moves:
            game.apply_move(m)
            value = min(value, minimax(game, depth - 1, alpha, beta, True))
            game.undo()
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


def best_move(game, max_depth=MAX_DEPTH, time_limit=TIME_LIMIT):
    moves = game.get_legal_moves()
    assert moves, "best_move appelé sans coups légaux"

    moves = order_moves(moves)
    chosen = moves[0]
    start  = time.time()

    maximizing_root = (game.get_state()[90] == 1)

    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break

        best_val   = -math.inf
        alpha      = -math.inf
        beta       =  math.inf
        depth_best = chosen

        for m in moves:
            if time.time() - start > time_limit:
                break
            game.apply_move(m)
            val = minimax(game, depth - 1, alpha, beta, not maximizing_root)
            game.undo()

            if val > best_val:
                best_val   = val
                depth_best = m
            alpha = max(alpha, best_val)

        chosen = depth_best
        elapsed = time.time() - start
        print(f"  [depth={depth}] coup={chosen}  score={best_val:.1f}  ({elapsed:.2f}s)")

        if best_val >= WIN_SCORE:
            break

    return chosen


def play_game(human_starts=True):
    game = engine.Game()
    move_number = 0

    print("\n=== Ultimate Tic Tac Toe - Minimax Alpha-Beta ===")
    print(f"  Humain {'commence (joueur 1/X)' if human_starts else 'est joueur 2/O'}")

    human_turn = human_starts

    while not game.is_done():
        move_number += 1
        legal = game.get_legal_moves()

        print("\nPlateau actuel :")
        game.print_board()   

        print(f"\n--- Coup {move_number} | {'Humain' if human_turn else 'IA'} ---")
        print(f"Coups légaux : {legal}")

        if human_turn:
            while True:
                try:
                    m = int(input("Votre coup (0-80) : "))
                    if m in legal:
                        break
                    print("  Coup illégal.")
                except ValueError:
                    print("  Entrez un entier.")

            game.apply_move(m)
            print(f"  -> Humain joue {m}")

        else:
            t0 = time.time()
            m = best_move(game)
            elapsed = time.time() - t0

            game.apply_move(m)
            print(f"  -> IA joue {m}  ({elapsed:.2f}s)")

        print("\nPlateau après le coup :")
        game.print_board()   

        human_turn = not human_turn

    print("\nPlateau final :")
    game.print_board()

    w = game.get_winner()
    print("\n=== Partie terminée ===")
    if w == 0:
        print("Match nul !")
    elif (w == 1 and human_starts) or (w == -1 and not human_starts):
        print("L'humain gagne !")
    else:
        print("L'IA gagne !")


if __name__ == "__main__":
    choice = input("Qui commence ? [h]umain / [i]a : ").strip().lower()
    play_game(human_starts=(choice != "i"))