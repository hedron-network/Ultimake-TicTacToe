# UTTT Neural Evaluator + Alpha-Beta

Train a neural network to evaluate positions in **Ultimate Tic-Tac-Toe**, then
use it as the heuristic inside an alpha-beta minimax search.

## Files

| File | Purpose |
|---|---|
| `uttt_model.py` | Neural network architecture |
| `selfplay.py` | Generate training data via random self-play |
| `train.py` | Train the evaluator |
| `alphabeta.py` | Alpha-beta agent that uses the trained model |
| `run_pipeline.py` | One-shot script that runs all three steps |

---

## Quick Start

### 1. Prerequisites

```bash
pip install torch          # CPU-only is fine for small runs
```

Your compiled `engine` module must be importable:
```bash
# e.g. if you built it with pybind11:
export PYTHONPATH=/path/to/your/engine/build:$PYTHONPATH
python -c "import engine; print('OK')"
```

---

### 2. Full pipeline (one command)

```bash
python run_pipeline.py --games 20000 --epochs 30 --depth 4
```

This will:
1. Play 20 000 random games and save positions to `data/selfplay.pt`
2. Train for 30 epochs and save the best checkpoint to `checkpoints/eval.pt`
3. Run a short alpha-beta demo game

---

### 3. Step by step

**Generate data**
```bash
python selfplay.py --games 20000 --out data/selfplay.pt
```

**Train**
```bash
python train.py \
    --data   data/selfplay.pt \
    --out    checkpoints/eval.pt \
    --epochs 30 \
    --hidden 256 \
    --layers 6
```

**Run alpha-beta demo**
```bash
python alphabeta.py --checkpoint checkpoints/eval.pt --depth 4
```

---

## Iterative refinement

Generate a second batch of games, combine with the first, retrain:
```bash
python selfplay.py --games 20000 --out data/selfplay2.pt
python train.py \
    --data data/selfplay.pt data/selfplay2.pt \
    --resume checkpoints/eval.pt \
    --out checkpoints/eval2.pt \
    --epochs 20
```

---

## Using the agent in your own code

```python
import engine
from alphabeta import AlphaBetaAgent

agent = AlphaBetaAgent("checkpoints/eval.pt", depth=4)
game  = engine.Game()

while not game.is_done():
    move = agent.best_move(game)   # returns an int 0-80
    game.apply_move(move)

print("Winner:", game.get_winner())
```

---

## Architecture

```
Input (406 floats)
  └─ Linear → LayerNorm → GELU          [projection]
       └─ × 6  ResidualBlock            [tower]
            └─ Linear → GELU → Linear → Tanh   [value head → scalar ∈ [-1,1]]
```

The 406-float state encodes:
- Plane 0 (81): current player's pieces on all 9 sub-boards
- Plane 1 (81): opponent's pieces
- Plane 2 (81): sub-boards won by current player (whole board = 1)
- Plane 3 (81): sub-boards won by opponent
- Plane 4 (81): valid target boards
- Scalar (1): current player indicator

---

## Alpha-Beta details

- **Negamax** formulation — value is always from the current mover's POV
- **Move ordering** — child positions are scored with the NN before searching,
  so the best moves are tried first (dramatically improves pruning)
- **Iterative deepening** — when a `time_limit` is passed to `best_move()`,
  the agent deepens until the clock runs out
- Terminal positions return ±1 (win/loss) exactly, bypassing the NN

```python
# Time-limited search (e.g. 2 seconds per move)
move = agent.best_move(game, time_limit=2.0)
```
