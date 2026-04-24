"""
alphabeta.py - Alpha-beta minimax search using the trained UTTTEvaluator.

The neural network provides a heuristic value (from the current player's POV).
Alpha-beta prunes branches using this heuristic at leaf nodes.

Usage
-----
    from alphabeta import AlphaBetaAgent
    import engine

    agent = AlphaBetaAgent("checkpoints/eval.pt", depth=4)
    game  = engine.Game()
    move  = agent.best_move(game)
    game.apply_move(move)
"""

import math
import time
import torch
from uttt_model import UTTTEvaluator


# ──────────────────────────────────────────────────────────────────────────────
# Evaluator wrapper
# ──────────────────────────────────────────────────────────────────────────────

class NNEvaluator:
    def __init__(self, checkpoint_path: str, device: str = "auto"):
        if device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        args = ckpt.get("args", {})

        self.model = UTTTEvaluator(
            hidden_dim=args.get("hidden", 256),
            num_residual=args.get("layers", 6),
            dropout=0.0,            # no dropout at inference
        ).to(self.device)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()

    @torch.no_grad()
    def __call__(self, state: list[float]) -> float:
        t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        return self.model(t).item()   # float in [-1, 1]


# ──────────────────────────────────────────────────────────────────────────────
# Alpha-Beta search
# ──────────────────────────────────────────────────────────────────────────────

class AlphaBetaAgent:
    """
    Negamax with alpha-beta pruning.

    The engine's get_state() is always from the current player's perspective,
    and get_winner() returns 1/-1 relative to player 1 (X).
    We normalise terminal values so that +1 always means "good for the node's mover".

    Parameters
    ----------
    checkpoint_path : str
        Path to a checkpoint saved by train.py.
    depth : int
        Search depth (plies). 4-6 is practical without GPU.
    move_order_depth : int
        Depth at which to score moves with the NN before sorting (move ordering).
    """

    def __init__(
        self,
        checkpoint_path: str,
        depth: int = 4,
        move_order_depth: int = 1,
        device: str = "auto",
    ):
        self.evaluator = NNEvaluator(checkpoint_path, device)
        self.depth = depth
        self.move_order_depth = move_order_depth
        self.nodes = 0

    # ── public interface ──────────────────────────────────────────────────────

    def best_move(self, game, time_limit: float = None) -> int:
        """
        Return the best move for the current player.
        Optionally respects a soft time_limit (seconds).
        """
        self.nodes = 0
        self._deadline = time.time() + time_limit if time_limit else None

        moves = game.get_legal_moves()
        if not moves:
            raise ValueError("No legal moves available")
        if len(moves) == 1:
            return moves[0]

        best_move = moves[0]
        best_score = -math.inf

        # Iterative deepening (useful when time_limit is set)
        max_depth = self.depth
        for d in range(1, max_depth + 1):
            score, mv = self._root_search(game, moves, d)
            if mv is not None:
                best_move, best_score = mv, score
            if self._deadline and time.time() > self._deadline:
                break

        return best_move

    # ── internal helpers ──────────────────────────────────────────────────────

    def _root_search(self, game, moves, depth):
        alpha = -math.inf
        beta  =  math.inf
        best_score = -math.inf
        best_move  = None

        ordered = self._order_moves(game, moves)

        for move in ordered:
            game.apply_move(move)
            # After apply_move the player has switched, so we negate the child score
            score = -self._negamax(game, depth - 1, -beta, -alpha)
            game.undo()

            if score > best_score:
                best_score = score
                best_move  = move
            alpha = max(alpha, score)

        return best_score, best_move

    def _negamax(self, game, depth: int, alpha: float, beta: float) -> float:
        self.nodes += 1

        # Terminal node
        if game.is_done():
            w = game.get_winner()  # 1, -1, or 0 — relative to player 1 (X)
            current = game.GetCurrentPlayer()
            # Negate because the LAST apply_move already switched the player,
            # so get_winner's winner is from the perspective of the player who just moved,
            # which is the opponent of the current node's mover.
            # Simpler: the game is done, the last mover won/lost.
            if w == 0:
                return 0.0
            # If current player is 1 (X) and X won, that's bad for current node
            # (current node is the one about to "move" but game is done – it lost).
            # From negamax POV: value is from the mover's perspective.
            # After is_done(), the player whose turn it would be is the loser (or draw).
            return -1.0 if w != 0 else 0.0

        if depth == 0:
            return self._leaf_value(game)

        if self._deadline and self.nodes % 1024 == 0 and time.time() > self._deadline:
            return self._leaf_value(game)

        moves = game.get_legal_moves()
        ordered = self._order_moves(game, moves)

        value = -math.inf
        for move in ordered:
            game.apply_move(move)
            child_val = -self._negamax(game, depth - 1, -beta, -alpha)
            game.undo()

            if child_val > value:
                value = child_val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break  # β-cutoff

        return value

    def _leaf_value(self, game) -> float:
        """NN evaluation; always from the current mover's perspective."""
        return self.evaluator(game.get_state())

    def _order_moves(self, game, moves: list[int]) -> list[int]:
        """
        Quick move ordering: score each child with the NN at depth 0,
        then return moves sorted best-first (for the current player).
        Only done when move count is manageable.
        """
        if len(moves) <= 1 or len(moves) > 40:
            return moves  # skip ordering for very many moves (first move etc.)

        scored = []
        for move in moves:
            game.apply_move(move)
            # child score from opponent's view → negate for us
            score = -self._leaf_value(game)
            game.undo()
            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]


# ──────────────────────────────────────────────────────────────────────────────
# Quick self-play demo
# ──────────────────────────────────────────────────────────────────────────────

def demo(checkpoint: str, depth: int = 4):
    try:
        import engine
    except ImportError:
        raise RuntimeError("Could not import 'engine'. Build the C++ extension first.")

    agent = AlphaBetaAgent(checkpoint, depth=depth)
    game  = engine.Game()

    print("=== Alpha-Beta UTTT Demo ===")
    print(f"Depth: {depth}\n")

    move_num = 0
    while not game.is_done():
        t0 = time.time()
        move = agent.best_move(game)
        elapsed = time.time() - t0

        board_idx = move // 9
        cell_idx  = move % 9
        player = "X" if game.GetCurrentPlayer() == 1 else "O"
        print(f"Move {move_num+1}: {player} plays board={board_idx} cell={cell_idx} "
              f"(move={move})  [{elapsed:.2f}s, {agent.nodes} nodes]")

        game.apply_move(move)
        move_num += 1

    game.PrintGame()
    w = game.get_winner()
    if w == 1:
        print("\n🏆 X wins!")
    elif w == -1:
        print("\n🏆 O wins!")
    else:
        print("\n🤝 Draw!")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--depth", type=int, default=4)
    args = p.parse_args()
    demo(args.checkpoint, args.depth)
