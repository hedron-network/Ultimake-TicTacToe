"""
run_pipeline.py - One-shot pipeline: generate data → train → evaluate.

    python run_pipeline.py --games 20000 --epochs 30 --depth 4

This script imports 'engine' for data generation but the trained model
and alpha-beta code work independently from that.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]):
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, check=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games",   type=int, default=20_000, help="Self-play games")
    parser.add_argument("--epochs",  type=int, default=30,     help="Training epochs")
    parser.add_argument("--depth",   type=int, default=4,      help="Alpha-beta depth for demo")
    parser.add_argument("--hidden",  type=int, default=256)
    parser.add_argument("--layers",  type=int, default=6)
    parser.add_argument("--data_dir", default="data")
    parser.add_argument("--ckpt_dir", default="checkpoints")
    args = parser.parse_args()

    data_file = f"{args.data_dir}/selfplay.pt"
    ckpt_file = f"{args.ckpt_dir}/eval.pt"

    Path(args.data_dir).mkdir(exist_ok=True)
    Path(args.ckpt_dir).mkdir(exist_ok=True)

    # Step 1: Generate self-play data
    run([
        sys.executable, "selfplay.py",
        "--games", str(args.games),
        "--out",   data_file,
    ])

    # Step 2: Train
    run([
        sys.executable, "train.py",
        "--data",   data_file,
        "--out",    ckpt_file,
        "--epochs", str(args.epochs),
        "--hidden", str(args.hidden),
        "--layers", str(args.layers),
    ])

    # Step 3: Demo
    run([
        sys.executable, "alphabeta.py",
        "--checkpoint", ckpt_file,
        "--depth",      str(args.depth),
    ])


if __name__ == "__main__":
    main()
