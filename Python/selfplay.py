# train.py
import torch
import torch.nn as nn
import engine, random, json
from main import best_move
from tqdm import tqdm

# ── Model ──────────────────────────────────────────────────────────────────
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

# ── Self-play data generation ───────────────────────────────────────────────
def generate_game(model, epsilon=0.15):
    game = engine.Game()
    history = []

    while not game.is_done():
        feats = extract_features(game)
        history.append((feats, game.get_current_player()))

        if random.random() < epsilon:
            m = random.choice(game.get_legal_moves())
        else:
            m = best_move(game)
        game.apply_move(m)

    winner = game.get_winner()

    samples = []
    for feats, player in history:
        if winner == 0:
            label = 0.0
        else:
            label = 1.0 if winner == player else -1.0
        samples.append((feats, label))
    return samples

# ── Training loop ───────────────────────────────────────────────────────────
def train(n_games=500, epochs_per_batch=10, batch_size=256, lr=1e-3, model=None):
    if model is None:
        model = GlobalEval()
    # ↑ removed the erroneous second model = GlobalEval() that was here

    opt     = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    all_samples = []
    last_loss   = float("nan")

    pbar = tqdm(range(n_games), desc="Self-play", unit="game")
    for game_i in pbar:
        epsilon = max(0.05, 0.3 - game_i / 1000)
        samples = generate_game(model, epsilon=epsilon)
        all_samples.extend(samples)

        if len(all_samples) > 50_000:
            all_samples = all_samples[-50_000:]

        if (game_i + 1) % 20 == 0:
            feats  = torch.tensor([s[0] for s in all_samples], dtype=torch.float32)
            labels = torch.tensor([s[1] for s in all_samples], dtype=torch.float32)

            dataset = torch.utils.data.TensorDataset(feats, labels)
            loader  = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

            model.train()
            for _ in range(epochs_per_batch):
                for xb, yb in loader:
                    pred = model(xb)
                    loss = loss_fn(pred, yb)
                    opt.zero_grad()
                    loss.backward()
                    opt.step()

            last_loss = loss.item()

        pbar.set_postfix(
            loss    = f"{last_loss:.4f}",
            buf     = len(all_samples),
            eps     = f"{epsilon:.2f}",
        )

    return model

# ── Export to JSON for C++ ──────────────────────────────────────────────────
def export_weights(model, path="./model_weights.json"):
    sd  = model.state_dict()
    out = {}
    layer_map = {"net.0": "fc1", "net.2": "fc2", "net.4": "fc3"}
    for pt_name, cpp_name in layer_map.items():
        out[f"{cpp_name}.weight"] = sd[f"{pt_name}.weight"].tolist()
        out[f"{cpp_name}.bias"]   = sd[f"{pt_name}.bias"].tolist()
    with open(path, "w") as f:
        json.dump(out, f)
    print(f"Saved to {path}")

# ── Load or initialise ──────────────────────────────────────────────────────
def load_or_init(path="./model_weights.json"):
    model = GlobalEval()
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

if __name__ == "__main__":
    model = load_or_init("./model_weights.json")
    model = train(n_games=500, model=model)
    export_weights(model, "./model_weights.json")