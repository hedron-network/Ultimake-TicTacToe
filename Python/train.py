"""
train.py - Train the UTTTEvaluator on self-play data.

Typical workflow
----------------
1. Generate data:
    python selfplay.py --games 20000 --out data/selfplay.pt

2. Train:
    python train.py --data data/selfplay.pt --epochs 30 --out checkpoints/eval.pt

3. Iterate (optional – generate more data with the trained net guiding play):
    python selfplay.py --games 20000 --model checkpoints/eval.pt --out data/selfplay2.pt
    python train.py --data data/selfplay.pt data/selfplay2.pt --epochs 20 --out checkpoints/eval2.pt
"""

import argparse
import math
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from uttt_model import UTTTEvaluator


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_datasets(paths: list[str]):
    all_states, all_values = [], []
    for p in paths:
        d = torch.load(p, weights_only=True)
        all_states.append(d["states"])
        all_values.append(d["values"])
    states = torch.cat(all_states, dim=0)
    values = torch.cat(all_values, dim=0)
    print(f"Loaded {len(states):,} positions from {len(paths)} file(s).")
    return states, values


def make_loaders(states, values, val_frac=0.05, batch_size=512):
    dataset = TensorDataset(states, values)
    val_size = max(1, int(len(dataset) * val_frac))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size * 4, shuffle=False, num_workers=0)
    return train_loader, val_loader


# ──────────────────────────────────────────────────────────────────────────────
# Training loop
# ──────────────────────────────────────────────────────────────────────────────

def train_epoch(model, loader, optimizer, criterion, device, grad_clip=1.0):
    model.train()
    total_loss = 0.0
    for states, values in loader:
        states, values = states.to(device), values.to(device)
        optimizer.zero_grad()
        pred = model(states)           # (B, 1)
        loss = criterion(pred, values) # MSE
        loss.backward()
        if grad_clip:
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        total_loss += loss.item() * len(states)
    return total_loss / len(loader.dataset)


@torch.no_grad()
def eval_epoch(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    for states, values in loader:
        states, values = states.to(device), values.to(device)
        pred = model(states)
        total_loss += criterion(pred, values).item() * len(states)
        # Sign accuracy: did we at least predict the right side?
        correct += ((pred.sign() == values.sign()) | (values == 0)).sum().item()
        total += len(states)
    return total_loss / len(loader.dataset), correct / total


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train UTTT position evaluator")
    parser.add_argument("--data",     nargs="+", required=True,
                        help="Path(s) to .pt files produced by selfplay.py")
    parser.add_argument("--out",      default="checkpoints/eval.pt",
                        help="Where to save the best checkpoint")
    parser.add_argument("--epochs",   type=int,   default=30)
    parser.add_argument("--lr",       type=float, default=3e-4)
    parser.add_argument("--batch",    type=int,   default=512)
    parser.add_argument("--hidden",   type=int,   default=256)
    parser.add_argument("--layers",   type=int,   default=6,
                        help="Number of residual blocks")
    parser.add_argument("--dropout",  type=float, default=0.1)
    parser.add_argument("--wd",       type=float, default=1e-4,
                        help="Weight decay")
    parser.add_argument("--resume",   default=None,
                        help="Resume training from this checkpoint")
    parser.add_argument("--device",   default="auto",
                        choices=["auto", "cpu", "cuda", "mps"])
    args = parser.parse_args()

    # Device
    if args.device == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(args.device)
    print(f"Using device: {device}")

    # Data
    states, values = load_datasets(args.data)
    train_loader, val_loader = make_loaders(states, values, batch_size=args.batch)
    print(f"  train: {len(train_loader.dataset):,}  val: {len(val_loader.dataset):,}")

    # Model
    model = UTTTEvaluator(
        hidden_dim=args.hidden,
        num_residual=args.layers,
        dropout=args.dropout,
    ).to(device)

    start_epoch = 0
    best_val_loss = math.inf

    if args.resume:
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state"])
        start_epoch = ckpt.get("epoch", 0)
        best_val_loss = ckpt.get("best_val_loss", math.inf)
        print(f"Resumed from {args.resume} (epoch {start_epoch}, best val {best_val_loss:.4f})")

    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {num_params:,}")

    # Optimizer + scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=args.lr / 20
    )
    criterion = nn.MSELoss()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'Epoch':>6}  {'Train Loss':>11}  {'Val Loss':>10}  {'Sign Acc':>9}  {'LR':>9}")
    print("-" * 55)

    for epoch in range(start_epoch + 1, start_epoch + args.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, sign_acc = eval_epoch(model, val_loader, criterion, device)
        scheduler.step()

        lr_now = optimizer.param_groups[0]["lr"]
        print(f"{epoch:>6}  {train_loss:>11.5f}  {val_loss:>10.5f}  {sign_acc:>9.3%}  {lr_now:>9.2e}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(
                {
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "best_val_loss": best_val_loss,
                    "args": vars(args),
                },
                args.out,
            )
            print(f"         ↑ saved best checkpoint → {args.out}")

    print(f"\nTraining complete. Best val loss: {best_val_loss:.5f}")


if __name__ == "__main__":
    main()
