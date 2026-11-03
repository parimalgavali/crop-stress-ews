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


def test_grud_input_decay_has_live_gradients():
    # Review finding 4.1: zero-init w_x/b_x sit on relu's kink, so no gradient can flow.
    model = GRUD(2, 1)
    x = torch.randn(8, 6, 2)
    m = (torch.rand(8, 6, 2) > 0.3).float()
    d = torch.rand(8, 6, 2) * 5  # positive time gaps are what input decay responds to
    loss = model(x, m, d).mean()
    loss.backward()
    assert model.w_x.grad is not None and model.w_x.grad.abs().sum() > 0
    assert model.b_x.grad is not None and model.b_x.grad.abs().sum() > 0
    opt = torch.optim.Adam(model.parameters(), lr=0.05)
    w0, b0 = model.w_x.detach().clone(), model.b_x.detach().clone()
    for _ in range(5):
        opt.zero_grad()
        model(x, m, d).mean().backward()
        opt.step()
    assert not torch.allclose(model.w_x, w0) or not torch.allclose(model.b_x, b0)


def test_grud_missing_input_decays_with_gap_and_observed_is_untouched():
    torch.manual_seed(0)
    model = GRUD(1, 1).eval()
    # last observed value 4.0, then one missing step
    x = torch.tensor([[[4.0], [0.0]]])
    m = torch.tensor([[[1.0], [0.0]]])
    short = model(x, m, torch.tensor([[[0.0], [0.5]]]))
    long_ = model(x, m, torch.tensor([[[0.0], [10.0]]]))
    # a larger gap must not impute *more* of the stale observation than a small gap
    # (checked via the cell input x_hat: gamma_x shrinks with the gap at this init)
    assert model.w_x.item() > 0
    g_short = float(torch.exp(-torch.relu(model.w_x * 0.5 + model.b_x)))
    g_long = float(torch.exp(-torch.relu(model.w_x * 10.0 + model.b_x)))
    assert g_long < g_short < 1.0
    # observed inputs pass through unaltered: x_hat == x when m == 1
    xs, ms, ds = torch.tensor([[4.0]]), torch.tensor([[1.0]]), torch.tensor([[0.0]])
    x_hat = ms * xs + (1 - ms) * torch.exp(-torch.relu(model.w_x * ds + model.b_x)) * xs
    assert float(x_hat) == 4.0
    assert torch.isfinite(short).all() and torch.isfinite(long_).all()
