import numpy as np
import pandas as pd

from cropews.config import HORIZONS_DAYS
from cropews.retrain import decide, fit_bundle, holdout_auroc


def test_decide_needs_a_mean_gain_without_a_clear_loss_at_any_horizon():
    champ = {7: 0.80, 14: 0.80, 21: 0.80}
    assert decide(champ, {7: 0.82, 14: 0.81, 21: 0.80})["promote"]
    assert not decide(champ, {7: 0.86, 14: 0.83, 21: 0.78})["promote"]
    assert not decide(champ, champ)["promote"]


def test_fit_bundle_scores_like_the_live_bundle_format():
    rng = np.random.default_rng(0)
    x = rng.normal(size=400)
    d = pd.DataFrame({"x": x, "noise": rng.normal(size=400)})
    for h in HORIZONS_DAYS:
        d[f"onset_{h}d"] = (x + rng.normal(scale=0.5, size=400) > 0.8).astype(float)
    bundle = fit_bundle(d[:200], d[200:300], ["x", "noise"])
    assert set(bundle["horizons"]) == set(HORIZONS_DAYS)
    assert bundle["horizons"][7]["red"] >= bundle["horizons"][7]["amber"]
    assert min(holdout_auroc(bundle, d[300:]).values()) > 0.8
