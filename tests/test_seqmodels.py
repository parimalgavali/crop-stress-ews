import numpy as np
import pytest

torch = pytest.importorskip("torch")

from cropews.seqmodels import GRUD, MaskedLSTM, fit, masked_bce, predict_logits  # noqa: E402


def _data(n: int = 200, steps: int = 6, c: int = 2, seed: int = 0) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, steps, c)).astype(np.float32)
    m = (rng.random((n, steps, c)) > 0.3).astype(np.float32)
    x *= m
    y = np.stack([(x[:, -1, 0] > 0), (x[:, -1, 0] > 0.5)], axis=1).astype(np.float32)
    y[:10, 1] = np.nan
    return {"x": x, "m": m, "d": np.zeros_like(x), "y": y}


@pytest.mark.parametrize("cls", [GRUD, MaskedLSTM])
def test_forward_shape_and_all_missing_is_finite(cls):
    model = cls(2, 3)
    x = torch.zeros(4, 5, 2)
    out = model(x, torch.zeros_like(x), torch.ones_like(x) * 3)
    assert out.shape == (4, 3) and torch.isfinite(out).all()


def test_masked_bce_ignores_undefined_targets():
    logits = torch.zeros(2, 2)
    y = torch.tensor([[1.0, float("nan")], [0.0, float("nan")]])
    assert torch.isclose(masked_bce(logits, y), torch.tensor(np.log(2), dtype=torch.float32))


def test_fit_learns_a_simple_signal():
    train, val = _data(seed=0), _data(seed=1)
    model = fit("grud", train, val, epochs=15, patience=15)
    z = predict_logits(model, val)[:, 0]
    y = val["y"][:, 0]
    assert z[y == 1].mean() > z[y == 0].mean()
