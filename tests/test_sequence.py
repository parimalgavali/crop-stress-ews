import numpy as np
import pandas as pd
import pytest

from cropews.sequence import (
    add_peer_channels,
    fit_scaler,
    mask_and_delta,
    model_inputs,
    row_index,
    to_sequences,
    windows,
)


def _frame(n_fields: int = 3, steps: int = 4) -> pd.DataFrame:
    dates = pd.date_range("2024-04-05", periods=steps, freq="5D")
    rows = [
        {
            "field_id": f"f{i}",
            "year": 2024,
            "district": "D",
            "date": d,
            "ndvi": 0.5 + 0.1 * i,
            "ndmi": 0.2,
            "ndre": 0.3,
            "onset_7d": 0.0,
            "onset_14d": np.nan,
            "onset_21d": 1.0,
        }
        for i in range(n_fields)
        for d in dates
    ]
    return pd.DataFrame(rows)


def test_windows_are_causal_and_left_padded():
    x = np.arange(6, dtype=np.float32).reshape(1, 6, 1)
    w = windows(x, 3)
    assert w.shape == (6, 3, 1)
    assert np.isnan(w[0, :2]).all() and w[0, 2, 0] == 0
    np.testing.assert_array_equal(w[4, :, 0], [2, 3, 4])
    x2 = x.copy()
    x2[0, 5] = 99
    np.testing.assert_array_equal(windows(x2, 3)[:5], w[:5])


def test_delta_counts_days_since_previous_observation():
    x = np.array([[[1.0], [np.nan], [np.nan], [2.0]]], dtype=np.float32)
    m, d = mask_and_delta(x)
    np.testing.assert_array_equal(m[0, :, 0], [1, 0, 0, 1])
    np.testing.assert_allclose(d[0, :, 0] * 30, [0, 5, 10, 15])


def test_to_sequences_shapes_and_row_index():
    seq = to_sequences(_frame(), ["ndvi"])
    assert seq.x.shape == (3, 4, 1) and seq.y.shape == (3, 4, 3)
    idx = row_index(seq)
    assert len(idx) == 12 and idx["field_id"].iloc[4] == "f1"


def test_to_sequences_rejects_ragged_seasons():
    f = _frame().iloc[:-1]
    with pytest.raises(ValueError):
        to_sequences(f, ["ndvi"])


def test_peer_channel_needs_enough_peers():
    f = add_peer_channels(_frame(n_fields=3), min_peers=3)
    np.testing.assert_allclose(f.loc[f.field_id == "f0", "ndvi_peer"], -0.1)
    assert add_peer_channels(_frame(n_fields=3), min_peers=4)["ndvi_peer"].isna().all()


def test_model_inputs_fill_missing_with_training_mean():
    x = np.array([[[1.0], [np.nan], [3.0]]], dtype=np.float32)
    mean, sd = fit_scaler(x)
    seq = to_sequences(_frame(n_fields=1, steps=3), ["ndvi"])
    seq.x = x
    out = model_inputs(seq, mean, sd, 3)
    assert out["x"][1, 2, 0] == 0 and out["m"][1, 2, 0] == 0
    assert not np.isnan(out["x"]).any()
