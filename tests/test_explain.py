import numpy as np
import pandas as pd

from cropews.baselines import logistic_model
from cropews.explain import contributions, level, reason_code, top_reasons


def test_reason_codes_map_feature_families():
    assert reason_code("ndmi_peer_anom") == "behind_neighbours"
    assert reason_code("water_balance_30d") == "dry_spell"
    assert reason_code("vh_db_asc_slope") == "radar_change"
    assert reason_code("missingindicator ndvi_last") == "no_clear_image"
    assert reason_code("ndvi_last") == "weak_canopy"


def test_level_thresholds():
    np.testing.assert_array_equal(
        level(np.array([0.01, 0.05, 0.2]), amber=0.04, red=0.1), ["green", "amber", "red"]
    )


def test_top_reasons_follow_the_driving_feature():
    rng = np.random.default_rng(0)
    x = pd.DataFrame(
        {"ndvi_peer_anom": rng.normal(size=400), "water_balance_30d": rng.normal(size=400)}
    )
    y = (x["ndvi_peer_anom"] < -1).astype(int)
    model = logistic_model().fit(x, y)
    row = pd.DataFrame({"ndvi_peer_anom": [-2.5], "water_balance_30d": [0.0]})
    reasons = top_reasons(contributions(model, row))[0]
    assert reasons[0]["code"] == "behind_neighbours" and reasons[0]["text_de"]
    calm = pd.DataFrame({"ndvi_peer_anom": [2.5], "water_balance_30d": [0.0]})
    assert all(r["code"] != "behind_neighbours" for r in top_reasons(contributions(model, calm))[0])
