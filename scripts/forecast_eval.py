"""Does a 5-day weather forecast help the risk model? (US-19, ADR 0019)

Archived ICON forecasts exist only from 2024, so: train with observed next-5-day weather
(a perfect forecast) on the training years, compare on 2022, then score 2024/2025 with the
archived ICON forecast as it was known on each date. Also reports ICON skill against HYRAS.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from train_baselines import load

from cropews.baselines import lightgbm_model, logistic_model
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.data.forecast import issued_features, observed_features
from cropews.evaluation import bootstrap_ci
from cropews.features import feature_columns

FC = ["fc_rain_5d", "fc_tmin_5d"]


def _weather(interim: Path) -> pd.DataFrame:
    frames = [pd.read_parquet(p) for p in sorted((interim / "weather").glob("weather_*.parquet"))]
    return pd.concat(frames, ignore_index=True).drop_duplicates(["field_id", "date"])


def _icon(interim: Path) -> pd.DataFrame:
    frames = []
    for p in sorted((interim / "forecast").glob("icon_*_*.parquet")):
        _, district, _ = p.stem.split("_")
        frames.append(issued_features(pd.read_parquet(p)).assign(district=district))
    return pd.concat(frames, ignore_index=True)


def skill(daily: pd.DataFrame, data: pd.DataFrame, icon: pd.DataFrame) -> dict[str, object]:
    obs = observed_features(daily).merge(
        data[["field_id", "district"]].drop_duplicates(), on="field_id"
    )
    obs = obs.groupby(["district", "date"])[FC].mean().reset_index()
    both = obs.merge(icon, on=["district", "date"], suffixes=("_obs", "_icon"))
    both = both[both["date"].dt.month.between(4, 7)]
    r = both[["fc_rain_5d_obs", "fc_rain_5d_icon"]].corr().iloc[0, 1]
    wet_obs, wet_icon = both["fc_rain_5d_obs"] >= 20, both["fc_rain_5d_icon"] >= 20
    out = {
        "n_issue_dates": len(both),
        "rain_5d_corr": float(r),
        "rain_5d_mae_mm": float((both["fc_rain_5d_obs"] - both["fc_rain_5d_icon"]).abs().mean()),
        "tmin_5d_mae_c": float((both["fc_tmin_5d_obs"] - both["fc_tmin_5d_icon"]).abs().mean()),
        "wet_20mm_hit_rate": float((wet_icon & wet_obs).sum() / max(wet_obs.sum(), 1)),
        "wet_20mm_false_rate": float((wet_icon & ~wet_obs).sum() / max(wet_icon.sum(), 1)),
    }
    print(json.dumps(out, indent=1))
    return out


def _auc(frame: pd.DataFrame, n: int) -> dict[str, object]:
    return {
        "auroc": float(roc_auc_score(frame["y"], frame["score"])),
        "ci": bootstrap_ci(frame, lambda s: float(roc_auc_score(s["y"], s["score"])), n=n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--interim", type=Path, default=Path("data/interim"))
    parser.add_argument("--out", type=Path, default=Path("outputs/forecast_eval.json"))
    parser.add_argument("--bootstrap", type=int, default=300)
    args = parser.parse_args()

    data = load(args.processed_dir)
    base = feature_columns(data.drop(columns=[c for c in data if c.startswith("onset_")]))
    base = [c for c in base if c != "in_event"]
    daily = _weather(args.interim)
    icon = _icon(args.interim)
    perfect = data.merge(observed_features(daily), on=["field_id", "date"], how="left")
    issued = data.merge(icon, on=["district", "date"], how="left")
    split = {y: name for name, years in SPLITS.items() for y in years}
    report: dict[str, object] = {"icon_skill": skill(daily, data, icon)}
    for h in HORIZONS_DAYS:
        t = f"onset_{h}d"
        rows: dict[str, object] = {}
        for name, make in (("logistic", logistic_model), ("lightgbm", lightgbm_model)):
            res: dict[str, object] = {}
            for label, cols in (("no_forecast", base), ("with_forecast", base + FC)):
                d = perfect.dropna(subset=[t]).assign(y=lambda x, t=t: x[t].astype(int))
                d = d.assign(split=d["year"].map(split))
                model = make().fit(d[d.split == "train"][cols], d[d.split == "train"]["y"])
                for s in ("validation", "test", "extra_check"):
                    ev = d[d.split == s]
                    if label == "with_forecast" and s != "validation":
                        ev = (
                            ev[ev["year"] >= 2024]
                            .drop(columns=FC)
                            .merge(
                                issued[["field_id", "date", *FC]],
                                on=["field_id", "date"],
                                how="left",
                            )
                        )
                        ev = ev.dropna(subset=FC)
                    res[f"{label}/{s}"] = _auc(
                        ev.assign(score=model.predict_proba(ev[cols])[:, 1]), args.bootstrap
                    )
                if label == "with_forecast":
                    ev = d[d.split == "test"]
                    ev = ev.assign(score=model.predict_proba(ev[cols])[:, 1])
                    res["with_perfect_forecast/test"] = _auc(ev, args.bootstrap)
            rows[name] = res
            print(
                f"{h:>2}d {name:<9} " + "  ".join(f"{k} {v['auroc']:.3f}" for k, v in res.items())
            )  # type: ignore[index]
        report[f"{h}d"] = rows
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=lambda v: np.asarray(v).tolist()))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
