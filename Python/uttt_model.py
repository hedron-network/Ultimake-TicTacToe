"""
uttt_model.py - Neural network architecture for UTTT position evaluation.
Input:  406-float state vector (from engine.Game.get_state())
Output: scalar in [-1, 1]  (1 = current player wins, -1 = current player loses)
"""

import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, size: int, dropout: float = 0.1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(size, size),
            nn.LayerNorm(size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(size, size),
            nn.LayerNorm(size),
        )
        self.act = nn.GELU()

    def forward(self, x):
        return self.act(x + self.block(x))


class UTTTEvaluator(nn.Module):
    """
    Policy-value network for UTTT.
    value_head  : scalar in [-1,1]  (used for alpha-beta)
    """

    def __init__(
        self,
        input_dim: int = 406,
        hidden_dim: int = 256,
        num_residual: int = 6,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

        self.residual_tower = nn.Sequential(
            *[ResidualBlock(hidden_dim, dropout) for _ in range(num_residual)]
        )

        # Value head: predicts win/loss for current player
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Linear(64, 1),
            nn.Tanh(),  # output in [-1, 1]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x : (batch, 406)
        returns value : (batch, 1)
        """
        h = self.input_proj(x)
        h = self.residual_tower(h)
        value = self.value_head(h)
        return value

    @torch.no_grad()
    def evaluate(self, state: list[float], device: str = "cpu") -> float:
        """Convenience method for alpha-beta: returns a float in [-1, 1]."""
        self.eval()
        t = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
        return self.forward(t).item()
