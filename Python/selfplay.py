# train.py
import torch
import torch.nn as nn
import engine, random, json
from main import best_move
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
            nn.Linear(90, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1),   nn.Tanh()
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

# ── Feature extraction ──────────────────────────────────────────────────────
def extract_features(game):
    return game.get_features()

# ── Single game (must be top-level for pickling across processes) ────────────
def generate_game_worker(epsilon):
    """
    Runs in a subprocess — no model passed in, uses whatever weights
    are on disk (C++ engine loads them at Game() construction).
    Returns list of (feats, label).
    """
    game    = engine.Game()
    history = []

    while not game.is_done():
        feats = extract_features(game)
        history.append((feats, game.get_current_player()))

        if random.random() < epsilon:
            m = random.choice(game.get_legal_moves())
        else:
            m = best_move(game)
        game.apply_move(m)

    winner  = game.get_winner()
    samples = []
    for feats, player in history:
        label = 0.0 if winner == 0 else (1.0 if winner == player else -1.0)
        samples.append((feats, label))
    return samples

# ── Parallel game batch ──────────────────────────────────────────────────────
def generate_games_parallel(n, epsilon, n_workers):
    """Generate n games across n_workers processes, returns flat sample list."""
    all_samples = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(generate_game_worker, epsilon) for _ in range(n)]
        for f in as_completed(futures):
            all_samples.extend(f.result())
    return all_samples

# ── Training loop ───────────────────────────────────────────────────────────
def train(n_games=500, epochs_per_batch=10, batch_size=256, lr=1e-3,
          model=None, games_per_batch=20, n_workers=None):
    if model is None:
        model = GlobalEval().to(device)
    if n_workers is None:
        n_workers = max(1, multiprocessing.cpu_count() - 1)

    print(f"Generating games with {n_workers} workers, {games_per_batch} games per batch")

    opt     = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    all_samples = []
    last_loss   = float("nan")
    n_batches   = n_games // games_per_batch

    pbar = tqdm(range(n_batches), desc="Training", unit="batch")
    for batch_i in pbar:
        epsilon = max(0.05, 0.3 - (batch_i * games_per_batch) / 1000)

        # ── Generate games in parallel ──
        new_samples = generate_games_parallel(games_per_batch, epsilon, n_workers)
        all_samples.extend(new_samples)

        if len(all_samples) > 50_000:
            all_samples = all_samples[-50_000:]

        # ── Train on buffer ──
        feats  = torch.tensor([s[0] for s in all_samples], dtype=torch.float32)
        labels = torch.tensor([s[1] for s in all_samples], dtype=torch.float32)

        dataset = torch.utils.data.TensorDataset(feats, labels)
        loader  = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model.train()
        for _ in range(epochs_per_batch):
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                pred   = model(xb)
                loss   = loss_fn(pred, yb)
                opt.zero_grad()
                loss.backward()
                opt.step()

        last_loss = loss.item()

        pbar.set_postfix(
            loss     = f"{last_loss:.4f}",
            buf      = len(all_samples),
            eps      = f"{epsilon:.2f}",
            games    = (batch_i + 1) * games_per_batch,
            new_samp = len(new_samples),
        )

        # ── Export weights so workers pick them up next batch ──
        export_weights(model, "./model_weights.json")

    return model

# ── Export to JSON for C++ ──────────────────────────────────────────────────
def export_weights(model, path="./model_weights.json"):
    sd        = model.cpu().state_dict()
    model.to(device)
    out       = {}
    layer_map = {"net.0": "fc1", "net.2": "fc2", "net.4": "fc3"}
    for pt_name, cpp_name in layer_map.items():
        out[f"{cpp_name}.weight"] = sd[f"{pt_name}.weight"].tolist()
        out[f"{cpp_name}.bias"]   = sd[f"{pt_name}.bias"].tolist()
    with open(path, "w") as f:
        json.dump(out, f)

# ── Load or initialise ──────────────────────────────────────────────────────
def load_or_init(path="./model_weights.json"):
    model = GlobalEval().to(device)
    try:
        with open(path) as f:
            data = json.load(f)
        sd        = model.state_dict()
        layer_map = {"fc1": "net.0", "fc2": "net.2", "fc3": "net.4"}
        for cpp_name, pt_name in layer_map.items():
            sd[f"{pt_name}.weight"] = torch.tensor(data[f"{cpp_name}.weight"])
            sd[f"{pt_name}.bias"]   = torch.tensor(data[f"{cpp_name}.bias"])
        model.load_state_dict(sd)
        print("Loaded existing weights")
    except (FileNotFoundError, KeyError):
        print("No existing weights found, starting fresh")
        export_weights(model, path)
    return model

# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model = load_or_init("./model_weights.json")
    model = train(
        n_games         = 500,
        games_per_batch = 20,   # how many games to generate in parallel per batch
        n_workers       = None, # None = auto (cpu_count - 1)
        model           = model,
    )
    export_weights(model, "./model_weights.json")
    print("Done")