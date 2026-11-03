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


def test_reasons_never_contradict_raw_values() -> None:
    # Review finding 4.4: a rising slope must never be described as "greenness dropping".
    rng = np.random.default_rng(1)
    x = pd.DataFrame({"ndvi_slope": rng.normal(size=300), "vpd_15d": rng.normal(size=300)})
    y = (x["ndvi_slope"] > 0.5).astype(int)  # risk rises when slope RISES
    model = logistic_model().fit(x, y)

    rising = pd.DataFrame({"ndvi_slope": [0.04], "vpd_15d": [0.0]})
    rs = top_reasons(contributions(model, rising), rising)[0]
    assert rs[0]["code"] == "greenness_dropping"
    assert rs[0]["kind"] == "attribution"
    assert "dropping" not in rs[0]["text_en"]

    falling = pd.DataFrame({"ndvi_slope": [-0.04], "vpd_15d": [0.0]})
    rs2 = top_reasons(contributions(model, falling), falling)[0]
    assert rs2[0]["kind"] == "fact"
    assert "dropping" in rs2[0]["text_en"]

    # missing-data claim requires real missingness: clean row falls back to attribution
    clean = pd.DataFrame({"ndvi_slope": [0.0], "vpd_15d": [2.0], "s2_days_since": [2.0]})
    xs = pd.concat([x, clean]).assign(s2_days_since=0.0)
    model2 = logistic_model().fit(
        xs[["ndvi_slope", "vpd_15d", "s2_days_since"]], np.r_[y.values, 0]
    )
    stale = pd.DataFrame({"ndvi_slope": [0.0], "vpd_15d": [0.0], "s2_days_since": [30.0]})
    rs3 = top_reasons(contributions(model2, stale), stale)[0]
    if any(r["code"] == "no_clear_image" for r in rs3):
        assert next(r for r in rs3 if r["code"] == "no_clear_image")["kind"] == "fact"


def test_reasons_never_contradict_the_data() -> None:
    # Review finding 4.4: a rising slope must never be described as "greenness dropping".
    rng = np.random.default_rng(1)
    x = pd.DataFrame({"ndvi_slope": rng.normal(size=300), "vpd_15d": rng.normal(size=300)})
    y = (x["ndvi_slope"] > 0.5).astype(int)  # risk rises when the slope RISES
    model = logistic_model().fit(x, y)

    rising = pd.DataFrame({"ndvi_slope": [0.04], "vpd_15d": [0.0]})
    rs = top_reasons(contributions(model, rising), rising)[0]
    assert rs[0]["code"] == "greenness_dropping"
    assert rs[0]["kind"] == "attribution"
    assert "dropping" not in rs[0]["text_en"]

    falling = pd.DataFrame({"ndvi_slope": [-0.04], "vpd_15d": [0.0]})
    rs2 = top_reasons(contributions(model, falling), falling)[0]
    assert rs2[0]["kind"] == "fact"
    assert "dropping" in rs2[0]["text_en"]


def test_missing_image_claim_requires_real_missingness() -> None:
    rng = np.random.default_rng(2)
    x = pd.DataFrame({"s2_days_since": rng.uniform(0, 40, 300), "ndvi_last": rng.normal(size=300)})
    y = (x["s2_days_since"] > 20).astype(int)
    model = logistic_model().fit(x, y)

    stale = pd.DataFrame({"s2_days_since": [30.0], "ndvi_last": [0.0]})
    rs = top_reasons(contributions(model, stale), stale)[0]
    assert rs[0]["code"] == "no_clear_image" and rs[0]["kind"] == "fact"

    fresh = pd.DataFrame({"s2_days_since": [2.0], "ndvi_last": [0.0]})
    rs2 = top_reasons(contributions(model, fresh), fresh)[0]
    if rs2 and rs2[0]["code"] == "no_clear_image":
        assert rs2[0]["kind"] == "attribution"
        assert "No clear" not in rs2[0]["text_en"]
