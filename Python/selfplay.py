# train.py
import torch
import torch.nn as nn
import engine, random, json
from main import best_move, best_move_train, _tt as main_tt

from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# ── Device ─────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ── Model ───────────────────────────────────────────────────────────────────
class GlobalEval(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(90, 256), nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1),   nn.Tanh()
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

# ── Feature extraction ──────────────────────────────────────────────────────
def extract_features(game):
    return game.get_features()

# ── Single game worker ───────────────────────────────────────────────────────
def generate_game_worker(epsilon):
    """
    KEY IMPROVEMENTS:
    1. Only label final position with full outcome
    2. Earlier positions get progressively weaker labels based on actual game progress
    3. More aggressive opponent mixing
    """
    game = engine.Game()
    game.reload_weights()

    history = []
    
    # More variety: 30% full random, 30% AI vs random, 40% self-play
    game_type = random.random()
    if game_type < 0.3:
        # Both players random
        epsilon = 1.0
    elif game_type < 0.6:
        # AI (p1) vs random (p2)
        vs_random = True
    else:
        # Self-play
        vs_random = False

    while not game.is_done():
        feats   = extract_features(game)
        current = game.get_current_player()
        history.append((feats, current))

        # Exploration
        is_random_turn = random.random() < epsilon
        
        if game_type < 0.3:  # fully random game
            is_random_turn = True
        elif vs_random and current != 1:
            is_random_turn = True

        if is_random_turn:
            m = random.choice(game.get_legal_moves())
        else:
            m = best_move_train(game)
        game.apply_move(m)

    winner = game.get_winner()
    n = len(history)
    samples = []
    
    for i, (feats, player) in enumerate(history):
        player_sign = 1 if player == 1 else -1
        
        # IMPROVED LABELING:
        # Only the last 30% of moves get strong labels
        # Earlier moves get exponentially weaker labels
        position_ratio = (i + 1) / n
        
        if position_ratio < 0.5:
            # Early game: very weak label
            discount = position_ratio * 0.2
        elif position_ratio < 0.7:
            # Mid game: moderate label
            discount = 0.1 + (position_ratio - 0.5) * 2.0
        else:
            # End game: strong label
            discount = 0.5 + (position_ratio - 0.7) * 1.67
        
        if winner == 0:
            label = 0.0
        else:
            raw_label = 1.0 if winner == player_sign else -1.0
            label = raw_label * discount

        samples.append((feats, label))

    return samples

# ── Parallel game batch ──────────────────────────────────────────────────────
def generate_games_parallel(n, epsilon, n_workers):
    all_samples = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(generate_game_worker, epsilon) for _ in range(n)]
        for f in as_completed(futures):
            all_samples.extend(f.result())
    return all_samples

# ── Win-rate benchmark ───────────────────────────────────────────────────────
def benchmark(n=20):
    """AI (player 1) vs random (player 2)"""
    import main
    wins = 0
    draws = 0
    for _ in range(n):
        main._tt.clear()
        game = engine.Game()
        game.reload_weights()
        turn = 1
        ai_player = 1

        while not game.is_done():
            legal = game.get_legal_moves()
            if turn == ai_player:
                m = best_move(game)
            else:
                m = random.choice(legal)
            game.apply_move(m)
            turn = 0 if turn == 1 else 1

        w = game.get_winner()
        if w == 1:
            wins += 1
        elif w == 0:
            draws += 1

    return wins / n, draws / n

# ── Training loop ────────────────────────────────────────────────────────────
def train(n_games=500, epochs_per_batch=8, batch_size=256, lr=1e-3,
          model=None, games_per_batch=20, n_workers=None,
          benchmark_every=5):
    """
    IMPROVEMENTS:
    1. Higher learning rate (1e-3) since we're learning from scratch
    2. More epochs per batch (8) with larger model
    3. Weight decay for regularization
    4. Learning rate scheduling
    """
    if model is None:
        model = GlobalEval().to(device)
    if n_workers is None:
        n_workers = max(1, multiprocessing.cpu_count() - 1)

    print(f"Generating games with {n_workers} workers, {games_per_batch} games per batch")

    # Weight decay for regularization
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode='min', factor=0.5, patience=3
    )
    
    loss_fn = nn.MSELoss()

    all_samples = []
    last_loss = float("nan")
    n_batches = n_games // games_per_batch

    pbar = tqdm(range(n_batches), desc="Training", unit="batch")
    for batch_i in pbar:
        # Slower epsilon decay
        epsilon = max(0.15, 0.5 - (batch_i * games_per_batch) / 2000)

        # Generate games
        new_samples = generate_games_parallel(games_per_batch, epsilon, n_workers)
        all_samples.extend(new_samples)

        # Keep larger buffer
        if len(all_samples) > 100_000:
            all_samples = all_samples[-100_000:]

        # Train
        feats = torch.tensor([s[0] for s in all_samples], dtype=torch.float32)
        labels = torch.tensor([s[1] for s in all_samples], dtype=torch.float32)

        dataset = torch.utils.data.TensorDataset(feats, labels)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model.train()
        epoch_losses = []
        for _ in range(epochs_per_batch):
            batch_losses = []
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                loss = loss_fn(pred, yb)
                opt.zero_grad()
                loss.backward()
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                batch_losses.append(loss.item())
            epoch_losses.append(sum(batch_losses) / len(batch_losses))

        last_loss = sum(epoch_losses) / len(epoch_losses)
        scheduler.step(last_loss)

        # Export weights
        export_weights(model, "./model_weights.json")

        pbar.set_postfix(
            loss=f"{last_loss:.4f}",
            buf=len(all_samples),
            eps=f"{epsilon:.2f}",
            games=(batch_i + 1) * games_per_batch,
            new_samp=len(new_samples),
            lr=f"{opt.param_groups[0]['lr']:.2e}"
        )

        # Benchmark
        if (batch_i + 1) % benchmark_every == 0:
            wr, dr = benchmark(20)
            tqdm.write(f"  [batch {batch_i+1}] Win rate: {wr:.0%}, Draw rate: {dr:.0%}")

    return model

# ── Export/Load functions (unchanged) ───────────────────────────────────────
def export_weights(model, path="./model_weights.json"):
    sd = model.cpu().state_dict()
    model.to(device)
    out = {}
    layer_map = {
        "net.0": "fc1", 
        "net.3": "fc2",  # Skip dropout layers
        "net.6": "fc3",
        "net.8": "fc4"
    }
    for pt_name, cpp_name in layer_map.items():
        out[f"{cpp_name}.weight"] = sd[f"{pt_name}.weight"].tolist()
        out[f"{cpp_name}.bias"] = sd[f"{pt_name}.bias"].tolist()
    with open(path, "w") as f:
        json.dump(out, f)

def load_or_init(path="./model_weights.json"):
    model = GlobalEval().to(device)
    try:
        with open(path) as f:
            data = json.load(f)
        sd = model.state_dict()
        layer_map = {
            "fc1": "net.0",
            "fc2": "net.3",
            "fc3": "net.6",
            "fc4": "net.8"
        }
        for cpp_name, pt_name in layer_map.items():
            sd[f"{pt_name}.weight"] = torch.tensor(data[f"{cpp_name}.weight"])
            sd[f"{pt_name}.bias"] = torch.tensor(data[f"{cpp_name}.bias"])
        model.load_state_dict(sd)
        print("Loaded existing weights")
    except (FileNotFoundError, KeyError) as e:
        print(f"No existing weights found ({e}), starting fresh")
        export_weights(model, path)
    return model

# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model = load_or_init("./model_weights.json")
    model = train(
        n_games=250,           # More games
        games_per_batch=20,
        epochs_per_batch=8,      # More epochs
        lr=1e-3,                 # Higher LR
        n_workers=None,
        benchmark_every=5,
        model=model,
    )
    export_weights(model, "./model_weights.json")
    
    # Test evaluation distribution
    model.eval()
    game = engine.Game()
    scores = []
    for _ in range(200):
        if game.is_done():
            break
        feats = torch.tensor(game.get_features(), dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            scores.append(model(feats).item())
        game.apply_move(random.choice(game.get_legal_moves()))

    print(f"\nEvaluation distribution:")
    print(f"  min={min(scores):.3f}  max={max(scores):.3f}  mean={sum(scores)/len(scores):.3f}")
    print("Done")