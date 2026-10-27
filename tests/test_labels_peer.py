import numpy as np
import pandas as pd
import pytest

from cropews.labels import fit_peer_scale, peer_residuals, score_peer


def _obs(year: int, shift: float, low_field_value: float | None = None) -> pd.DataFrame:
    rows = []
    for k in range(10):
        ndvi = 0.8 + shift + 0.01 * (-1) ** k
        if k == 0 and low_field_value is not None:
            ndvi = low_field_value
        rows.append(
            {
                "field_id": f"f{k}",
                "year": year,
                "district": "D",
                "date": pd.Timestamp(f"{year}-05-10"),
                "doy_bin": 12,
                "ndvi": ndvi,
                "ndmi": 0.3 + shift,
            }
        )
    return pd.DataFrame(rows)


def test_season_wide_shift_cancels_out():
    a, b = peer_residuals(_obs(2019, 0.0)), peer_residuals(_obs(2022, -0.2))
    np.testing.assert_allclose(a["r_ndvi"], b["r_ndvi"])
    assert b["r_ndmi"].abs().max() == pytest.approx(0.0)


def test_dates_with_too_few_peers_are_dropped():
    assert peer_residuals(_obs(2019, 0.0).head(5)).empty


def test_scale_uses_training_years_only_and_flags_low_peer():
    obs = pd.concat([_obs(y, 0.0) for y in (2019, 2020, 2021)] + [_obs(2024, 0.0, 0.5)])
    res = peer_residuals(obs)
    scale = fit_peer_scale(res, (2019, 2020, 2021))
    scored = score_peer(res, scale)
    assert scored["below"].sum() == 1
    flagged = scored[scored["below"]].iloc[0]
    assert (flagged["field_id"], flagged["year"]) == ("f0", 2024)
    with pytest.raises(ValueError):
        fit_peer_scale(res, (2030,))
