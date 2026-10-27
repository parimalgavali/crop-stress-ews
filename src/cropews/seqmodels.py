"""GRU-D-style masked GRU and an LSTM baseline (ADR 0011). Requires the ``seq`` extra (torch)."""

from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn


class GRUD(nn.Module):
    """GRU-D (Che et al., 2018): missing inputs decay from the last observation towards the
    training mean (0 after standardising) and the hidden state decays with the time gap."""

    def __init__(self, n_in: int, n_out: int, hidden: int = 32, dropout: float = 0.2) -> None:
        super().__init__()
        self.w_x = nn.Parameter(torch.zeros(n_in))
        self.b_x = nn.Parameter(torch.zeros(n_in))
        self.decay_h = nn.Linear(n_in, hidden)
        self.cell = nn.GRUCell(2 * n_in, hidden)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, n_out))
        self.hidden = hidden

    def forward(self, x: torch.Tensor, m: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        b, steps, _ = x.shape
        h = x.new_zeros(b, self.hidden)
        last = torch.zeros_like(x[:, 0])
        for s in range(steps):
            xs, ms, ds = x[:, s], m[:, s], d[:, s]
            gamma_x = torch.exp(-torch.relu(self.w_x * ds + self.b_x))
            x_hat = ms * xs + (1 - ms) * gamma_x * last
            last = ms * xs + (1 - ms) * last
            h = torch.exp(-torch.relu(self.decay_h(ds))) * h
            h = self.cell(torch.cat([x_hat, ms], dim=1), h)
        return self.head(h)


class MaskedLSTM(nn.Module):
    """LSTM on [value (0 if missing), mask, time gap]; no decay mechanism."""

    def __init__(self, n_in: int, n_out: int, hidden: int = 32, dropout: float = 0.2) -> None:
        super().__init__()
        self.lstm = nn.LSTM(3 * n_in, hidden, batch_first=True)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, n_out))

    def forward(self, x: torch.Tensor, m: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(torch.cat([x, m, d], dim=2))
        return self.head(out[:, -1])


ARCHS = {"grud": GRUD, "lstm": MaskedLSTM}


def masked_bce(
    logits: torch.Tensor, y: torch.Tensor, pos_weight: torch.Tensor | None = None
) -> torch.Tensor:
    """Mean BCE over defined targets only (NaN = undefined horizon)."""
    ok = ~torch.isnan(y)
    loss = nn.functional.binary_cross_entropy_with_logits(
        logits[ok], y[ok], pos_weight=None if pos_weight is None else pos_weight.expand_as(y)[ok]
    )
    return loss


def _tensors(data: dict[str, np.ndarray]) -> list[torch.Tensor]:
    return [torch.from_numpy(np.ascontiguousarray(data[k])) for k in ("x", "m", "d", "y")]


def predict_logits(model: nn.Module, data: dict[str, np.ndarray], batch: int = 4096) -> np.ndarray:
    model.eval()
    x, m, d, _ = _tensors(data)
    with torch.no_grad():
        out = [
            model(x[i : i + batch], m[i : i + batch], d[i : i + batch])
            for i in range(0, len(x), batch)
        ]
    return torch.cat(out).numpy()


def fit(
    arch: str,
    train: dict[str, np.ndarray],
    val: dict[str, np.ndarray],
    seed: int = 0,
    epochs: int = 40,
    patience: int = 6,
    lr: float = 1e-3,
    batch: int = 256,
) -> nn.Module:
    """Adam with class-balanced masked BCE; keeps the epoch with the lowest validation loss."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    keep = ~np.isnan(train["y"]).all(axis=1)
    x, m, d, y = (t[torch.from_numpy(keep)] for t in _tensors(train))
    pos = torch.nansum(y, dim=0)
    neg = (~torch.isnan(y)).sum(dim=0) - pos
    pos_weight = (neg / pos.clamp(min=1)).clamp(max=50)
    model = ARCHS[arch](x.shape[2], y.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    vx, vm, vd, vy = _tensors(val)
    best, best_loss, bad = copy.deepcopy(model.state_dict()), float("inf"), 0
    for _ in range(epochs):
        model.train()
        order = torch.from_numpy(rng.permutation(len(x)))
        for i in range(0, len(x), batch):
            j = order[i : i + batch]
            opt.zero_grad()
            masked_bce(model(x[j], m[j], d[j]), y[j], pos_weight).backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        with torch.no_grad():
            loss = float(masked_bce(model(vx, vm, vd), vy))
        if loss < best_loss - 1e-4:
            best, best_loss, bad = copy.deepcopy(model.state_dict()), loss, 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best)
    return model
