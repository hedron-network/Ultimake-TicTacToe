"""
selfplay.py - Generate training data through random / MCTS-lite self-play.

Each sample is (state_406, value) where value is:
  +1  if the player to move eventually won the game
  -1  if the player to move eventually lost
   0  if the game was drawn

Run standalone:
    python selfplay.py --games 5000 --out data/selfplay.pt
"""

import argparse
import random
import torch
from pathlib import Path


def play_random_game(engine_cls):
    """
    Play a fully random game.
    Returns list of (state, current_player_at_state) pairs, plus final winner.
    """
    game = engine_cls()
    trajectory = []

    while not game.is_done():
        state = game.get_state()
        player = game.GetCurrentPlayer()
        trajectory.append((state, player))

        moves = game.get_legal_moves()
        move = random.choice(moves)
        game.apply_move(move)

    winner = game.get_winner()  # 1 or -1 or 0 relative to player 1 (X)
    return trajectory, winner


def trajectory_to_samples(trajectory, winner):
    """
    Convert a trajectory to (state, value) pairs.
    value is from the perspective of the player to move at that state.
      winner = 1  → X (player 1) won
      winner = -1 → O (player 0) won
      winner = 0  → draw
    """
    samples = []
    for state, player in trajectory:
        if winner == 0:
            value = 0.0
        elif winner == 1:
            # player==1 means it was X's turn → X wins → value = +1
            value = 1.0 if player == 1 else -1.0
        else:
            # winner == -1 → O won
            value = -1.0 if player == 1 else 1.0
        samples.append((state, value))
    return samples


def generate_dataset(engine_cls, num_games: int, verbose: bool = True):
    states = []
    values = []

    for g in range(num_games):
        trajectory, winner = play_random_game(engine_cls)
        samples = trajectory_to_samples(trajectory, winner)
        for s, v in samples:
            states.append(s)
            values.append(v)

        if verbose and (g + 1) % max(1, num_games // 20) == 0:
            print(f"  [{g+1}/{num_games}] games done, {len(states)} positions collected")

    states_t = torch.tensor(states, dtype=torch.float32)
    values_t = torch.tensor(values, dtype=torch.float32).unsqueeze(1)
    return states_t, values_t


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10_000)
    parser.add_argument("--out", type=str, default="data/selfplay.pt")
    args = parser.parse_args()

    try:
        import engine
        engine_cls = engine.Game
    except ImportError:
        raise RuntimeError(
            "Could not import 'engine'. "
            "Make sure the compiled UTTT engine is on PYTHONPATH."
        )

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    print(f"Generating {args.games} random self-play games …")
    states, values = generate_dataset(engine_cls, args.games)
    torch.save({"states": states, "values": values}, args.out)
    print(f"Saved {len(states)} positions → {args.out}")
    print(f"  state shape : {states.shape}")
    print(f"  value shape : {values.shape}")
    print(f"  value dist  : +1={( values==1).sum().item()}  "
          f"-1={(values==-1).sum().item()}  "
          f"0={(values==0).sum().item()}")


if __name__ == "__main__":
    main()
