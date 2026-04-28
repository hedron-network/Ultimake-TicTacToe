"""
benchmark.py — per-function profiler for the Ultimate Tic Tac Toe engine.

Usage:
    python benchmark.py              # runs all benchmarks
    python benchmark.py --depth 5    # override search depth
    python benchmark.py --time 2.0   # override time limit
"""

import argparse
import cProfile
import io
import math
import pstats
import time
from collections import defaultdict

import engine

# ---------------------------------------------------------------------------
# Copy of the search constants / helpers (keep in sync with your main file)
# ---------------------------------------------------------------------------
WIN_SCORE  =  1_000_000
LOSS_SCORE = -1_000_000

_MOVE_PRIORITY = [
    2 if (i % 9) in {1, 3, 5, 7} else (0 if (i % 9) == 4 else 1)
    for i in range(81)
]

def order_moves(moves):
    return sorted(moves, key=_MOVE_PRIORITY.__getitem__)

# ---------------------------------------------------------------------------
# Shared counters — populated by the instrumented minimax below
# ---------------------------------------------------------------------------
_timings : dict[str, float] = defaultdict(float)
_counts  : dict[str, int]   = defaultdict(int)
_tt_hits = 0
_tt_misses = 0
_tt: dict = {}

_EXACT, _LOWER, _UPPER = 0, 1, 2


def _t(label: str, fn, *args, **kwargs):
    """Call fn(*args, **kwargs), accumulate wall-time under label."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    _timings[label] += time.perf_counter() - t0
    _counts[label]  += 1
    return result


# ---------------------------------------------------------------------------
# Instrumented minimax (mirrors your production version exactly)
# ---------------------------------------------------------------------------
def minimax_instrumented(game, depth, alpha, beta, maximizing):
    global _tt_hits, _tt_misses

    if _t("is_done", game.is_done):
        w = _t("get_winner", game.get_winner)
        if w == 1:   return WIN_SCORE
        if w == -1:  return LOSS_SCORE
        return 0

    if depth == 0:
        raw = _t("eval", game.eval) * 900_000
        return raw if maximizing else -raw

    moves = _t("get_legal_moves", game.get_legal_moves)
    if not moves:
        return 0

    h = _t("get_hash", game.get_hash)
    state_key = (h, maximizing)
    tt_entry  = _tt.get(state_key)

    if tt_entry is not None:
        _tt_hits += 1
        cached_depth, flag, cached_val = tt_entry
        if cached_depth >= depth:
            if flag == _EXACT:
                return cached_val
            elif flag == _LOWER:
                if cached_val > alpha:
                    alpha = cached_val
            else:
                if cached_val < beta:
                    beta = cached_val
            if alpha >= beta:
                return cached_val
    else:
        _tt_misses += 1

    moves = order_moves(moves)
    original_alpha = alpha

    if maximizing:
        value = -math.inf
        for m in moves:
            _t("apply_move", game.apply_move, m)
            child = minimax_instrumented(game, depth - 1, alpha, beta, False)
            _t("undo", game.undo)
            if child > value:
                value = child
                if value > alpha:
                    alpha = value
                    if alpha >= beta:
                        break
    else:
        value = math.inf
        for m in moves:
            _t("apply_move", game.apply_move, m)
            child = minimax_instrumented(game, depth - 1, alpha, beta, True)
            _t("undo", game.undo)
            if child < value:
                value = child
                if value < beta:
                    beta = value
                    if beta <= alpha:
                        break

    if value <= original_alpha:
        flag = _UPPER
    elif value >= beta:
        flag = _LOWER
    else:
        flag = _EXACT
    _tt[state_key] = (depth, flag, value)

    return value


def best_move_instrumented(game, max_depth=6, time_limit=9999.0):
    moves = game.get_legal_moves()
    assert moves, "best_move called with no legal moves"

    moves   = order_moves(moves)
    chosen  = moves[0]
    start   = time.monotonic()
    state   = game.get_state()
    maximizing_root = (state[90] == 1)

    ASPIRATION_DELTA = 50_000
    prev_score = 0

    for depth in range(1, max_depth + 1):
        if time.monotonic() - start > time_limit:
            break

        alpha = prev_score - ASPIRATION_DELTA if depth > 1 else -math.inf
        beta  = prev_score + ASPIRATION_DELTA if depth > 1 else  math.inf

        best_val   = -math.inf
        depth_best = chosen
        timeout    = False

        if depth > 1 and chosen in moves:
            moves.remove(chosen)
            moves.insert(0, chosen)

        while True:
            best_val   = -math.inf
            depth_best = chosen

            for m in moves:
                if time.monotonic() - start > time_limit:
                    timeout = True
                    break
                game.apply_move(m)
                val = minimax_instrumented(game, depth - 1, alpha, beta, not maximizing_root)
                game.undo()
                if val > best_val:
                    best_val   = val
                    depth_best = m
                if val > alpha:
                    alpha = val

            if timeout:
                break

            if depth > 1 and best_val <= prev_score - ASPIRATION_DELTA:
                alpha = -math.inf
                beta  = best_val + 1
            elif depth > 1 and best_val >= prev_score + ASPIRATION_DELTA:
                alpha = best_val - 1
                beta  = math.inf
            else:
                break

        if not timeout:
            chosen     = depth_best
            prev_score = best_val

    return chosen


# ---------------------------------------------------------------------------
# Pretty printers
# ---------------------------------------------------------------------------
SEP = "─" * 72

def print_header(title: str):
    print(f"\n{'═' * 72}")
    print(f"  {title}")
    print('═' * 72)

def print_timing_table():
    print_header("Per-Function Timing Breakdown")
    total_accounted = sum(_timings.values())

    print(f"  {'Function':<22} {'Calls':>10} {'Total (s)':>11} {'Per call (µs)':>14} {'Share':>8}")
    print(f"  {SEP}")

    for fn, secs in sorted(_timings.items(), key=lambda x: x[1], reverse=True):
        n       = _counts[fn]
        per_us  = secs / n * 1e6 if n else 0
        share   = secs / total_accounted * 100 if total_accounted else 0
        print(f"  {fn:<22} {n:>10,} {secs:>11.4f} {per_us:>14.2f} {share:>7.1f}%")

    print(f"\n  Total accounted: {total_accounted:.4f}s")


def print_tt_stats():
    print_header("Transposition Table Stats")
    total   = _tt_hits + _tt_misses
    hit_pct = _tt_hits / total * 100 if total else 0.0
    print(f"  Lookups : {total:>10,}")
    print(f"  Hits    : {_tt_hits:>10,}  ({hit_pct:.1f}%)")
    print(f"  Misses  : {_tt_misses:>10,}  ({100 - hit_pct:.1f}%)")
    print(f"  TT size : {len(_tt):>10,} entries")
    if hit_pct < 30:
        print("\n  ⚠  Low hit rate — get_hash() may return poor keys,")
        print("     or the TT is being thrashed between depths.")
    elif hit_pct > 70:
        print("\n  ✓  Excellent hit rate.")


def print_cprofile(pr: cProfile.Profile):
    print_header("cProfile — Top 25 by Cumulative Time")
    s  = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(25)
    # indent every line for readability
    for line in s.getvalue().splitlines():
        print("  " + line)


def print_isolated_benchmarks():
    """
    Micro-benchmark each engine call in isolation on a fresh game,
    so we know the raw cost independent of search branching.
    """
    print_header("Isolated Engine-Call Micro-Benchmarks  (10 000 iterations each)")

    game  = engine.Game()
    REPS  = 10_000
    results = {}

    # is_done
    t0 = time.perf_counter()
    for _ in range(REPS): game.is_done()
    results["is_done"] = (time.perf_counter() - t0) / REPS

    # get_legal_moves
    t0 = time.perf_counter()
    for _ in range(REPS): game.get_legal_moves()
    results["get_legal_moves"] = (time.perf_counter() - t0) / REPS

    # get_hash
    t0 = time.perf_counter()
    for _ in range(REPS): game.get_hash()
    results["get_hash"] = (time.perf_counter() - t0) / REPS

    # eval
    t0 = time.perf_counter()
    for _ in range(REPS): game.eval()
    results["eval"] = (time.perf_counter() - t0) / REPS

    # get_state
    t0 = time.perf_counter()
    for _ in range(REPS): game.get_state()
    results["get_state"] = (time.perf_counter() - t0) / REPS

    # apply_move + undo  (paired so state doesn't drift)
    moves = game.get_legal_moves()
    m = moves[0]
    t0 = time.perf_counter()
    for _ in range(REPS):
        game.apply_move(m)
        game.undo()
    pair_time = (time.perf_counter() - t0) / REPS
    results["apply_move"] = pair_time / 2
    results["undo"]       = pair_time / 2

    # get_winner  (cheap to call on a live game)
    t0 = time.perf_counter()
    for _ in range(REPS): game.get_winner()
    results["get_winner"] = (time.perf_counter() - t0) / REPS

    print(f"\n  {'Function':<22} {'Per call (µs)':>14}  {'Per call (ns)':>14}")
    print(f"  {SEP}")
    for fn, secs in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {fn:<22} {secs*1e6:>14.3f}  {secs*1e9:>14.0f}")

    # Highlight slow calls
    print()
    THRESHOLD_US = 5.0
    slow = {k: v for k, v in results.items() if v * 1e6 > THRESHOLD_US}
    if slow:
        print(f"  ⚠  Calls exceeding {THRESHOLD_US:.0f} µs (likely bottlenecks):")
        for fn, secs in sorted(slow.items(), key=lambda x: x[1], reverse=True):
            print(f"     • {fn}  →  {secs*1e6:.2f} µs")
    else:
        print(f"  ✓  All isolated calls are under {THRESHOLD_US:.0f} µs.")


def print_branching_factor():
    """Estimate average branching factor at each ply."""
    print_header("Branching Factor Estimate  (depth 3 from start)")
    game   = engine.Game()
    counts = defaultdict(int)
    calls  = defaultdict(int)

    def walk(g, d, max_d):
        if g.is_done() or d > max_d:
            return
        moves = g.get_legal_moves()
        counts[d] += len(moves)
        calls[d]  += 1
        for m in moves:
            g.apply_move(m)
            walk(g, d + 1, max_d)
            g.undo()

    walk(game, 0, 3)
    print(f"\n  {'Ply':<6} {'Positions':>10} {'Total moves':>12} {'Avg branch':>12}")
    print(f"  {SEP}")
    for d in sorted(counts):
        c = calls[d]
        t = counts[d]
        print(f"  {d:<6} {c:>10,} {t:>12,} {t/c:>12.1f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _tt, _tt_hits, _tt_misses

    parser = argparse.ArgumentParser(description="Benchmark the UTTT engine")
    parser.add_argument("--depth", type=int,   default=6,   help="Max search depth")
    parser.add_argument("--time",  type=float, default=9999, help="Time limit (s)")
    args = parser.parse_args()

    # 1 — Isolated micro-benchmarks (no search overhead)
    print_isolated_benchmarks()

    # 2 — Branching factor analysis
    print_branching_factor()

    # 3 — Full instrumented search (per-function totals inside real search)
    print_header(f"Instrumented Search  (depth={args.depth}, time={args.time}s)")
    _tt.clear()
    _tt_hits = _tt_misses = 0
    for k in list(_timings): del _timings[k]
    for k in list(_counts):  del _counts[k]

    game  = engine.Game()
    t0    = time.perf_counter()
    best_move_instrumented(game, max_depth=args.depth, time_limit=args.time)
    total = time.perf_counter() - t0
    print(f"\n  Search completed in {total:.3f}s")

    print_timing_table()
    print_tt_stats()

    # 4 — cProfile on the same search (catches Python overhead invisible above)
    print_header(f"cProfile Run  (depth={args.depth})")
    _tt.clear()
    _tt_hits = _tt_misses = 0

    game2 = engine.Game()
    pr    = cProfile.Profile()
    pr.enable()
    best_move_instrumented(game2, max_depth=args.depth, time_limit=args.time)
    pr.disable()
    print_cprofile(pr)

    print(f"\n{'═' * 72}")
    print("  Benchmark complete.")
    print('═' * 72 + "\n")


if __name__ == "__main__":
    main()
