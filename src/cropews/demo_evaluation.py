"""Reproducible mini-run on a synthetic fixture (review finding 4.8 / spec 8.5).

``python -m cropews.demo_evaluation`` runs the whole causal chain offline: synthetic field
observations → peer scoring → event extraction → horizon labels → baseline model → AUROC +
horizon-aware lead time. Prints a run manifest so a reviewer can verify the mechanics without
network access or licensed data. The fixture is deterministic and flagged synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from typing import Any

import numpy as np  # noqa: E402
import pandas as pd

from cropews.baselines import logistic_model
from cropews.errors import lead_times
from cropews.labels import find_events, make_targets, peer_residuals, score_peer

N_FIELDS = 40
DATES = pd.date_range("2024-04-05", "2024-06-25", freq="5D")
DOY_BIN = 10


def synthetic_observations(seed: int = 0) -> pd.DataFrame:
    """Clear S2-like observations; ~1/4 of fields get a two-step ndvi+ndmi dip (an 'event')."""
    rng = np.random.default_rng(seed)
    rows = []
    for f in range(N_FIELDS):
        dip_start = rng.integers(6, 14) if f % 4 == 0 else -1
        for i, d in enumerate(DATES):
            dip = dip_start >= 0 and i >= dip_start
            rows.append(
                {
                    "field_id": f"SYN{f:03d}",
                    "year": 2024,
                    "district": "SynKreis",
                    "date": d,
                    "doy_bin": int(d.dayofyear // DOY_BIN * DOY_BIN),
                    "clear_fraction": 1.0,
                    "ndvi": 0.7 + rng.normal(0, 0.02) - (0.18 if dip else 0),
                    "ndmi": 0.4 + rng.normal(0, 0.02) - (0.12 if dip else 0),
                    "ndre": 0.5 + rng.normal(0, 0.02) - (0.1 if dip else 0),
                }
            )
    return pd.DataFrame(rows)


def run(seed: int = 0) -> dict[str, Any]:
    started = time.monotonic()
    obs = synthetic_observations(seed)
    res = peer_residuals(obs, min_peers=8)
    scale = (
        res.groupby(["district", "doy_bin"])
        .agg(r_ndvi_std=("r_ndvi", "std"), r_ndmi_std=("r_ndmi", "std"), n=("ndvi", "size"))
        .reset_index()
    )
    scored = score_peer(res, scale)
    events = find_events(scored)

    targets = make_targets(scored[["field_id", "year", "date"]], events, scored)
    f = targets.merge(scored[["field_id", "date", "z_ndvi"]], on=["field_id", "date"]).rename(
        columns={"z_ndvi": "score"}
    )
    train_fids = sorted(f["field_id"].unique())[: N_FIELDS // 2]
    tr, te = f[f["field_id"].isin(train_fids)], f[~f["field_id"].isin(train_fids)]

    out: dict[str, Any] = {
        "synthetic": True,
        "seed": seed,
        "fields": N_FIELDS,
        "observations": len(obs),
        "parameters": {
            "horizons_days": [7, 14, 21],
            "dip": {"ndvi": 0.18, "ndmi": 0.12, "ndre": 0.1},
            "split": "first half of sorted field_ids is train",
            "min_peers": 8,
            "doy_bin": DOY_BIN,
        },
        "events": len(events),
        "horizons": {},
    }
    preds = []
    for h in (7, 14, 21):
        col = f"onset_{h}d"
        tr_h, te_h = tr.dropna(subset=[col]), te.dropna(subset=[col])
        model = logistic_model().fit(tr_h[["score"]], tr_h[col])
        p = model.predict_proba(te_h[["score"]])[:, 1]
        from sklearn.metrics import roc_auc_score

        auroc = float(roc_auc_score(te_h[col], p)) if te_h[col].nunique() == 2 else None
        thr = float(np.quantile(model.predict_proba(tr_h[["score"]])[:, 1], 0.9))
        preds.append(
            te_h[["field_id", "year", "date"]].assign(
                horizon_days=h,
                level=np.where(p >= thr, "red", "green"),
            )
        )
        out["horizons"][str(h)] = {"auroc": round(auroc, 3) if auroc else None, "n": len(te_h)}
    lt = lead_times(
        targets[["field_id", "year", "date", "in_event"]], pd.concat(preds), events=events
    )
    warned = lt["lead_days"].notna()
    out["lead_time"] = {
        "events": len(lt),
        "warned": int(warned.sum()),
        "median_days": float(lt["lead_days"].median()) if warned.any() else None,
    }
    out["runtime_seconds"] = round(time.monotonic() - started, 2)
    return out


# Keys that change between identical runs and are excluded from the expected-output diff
# and the artifact hash (spec 8.5: expected output files + artifact hashes).
VOLATILE = ("runtime_seconds", "python")


def _stable(manifest: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in manifest.items() if k not in VOLATILE}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", help="diff against an expected manifest, ignoring volatile keys")
    args = ap.parse_args()
    manifest = run()
    manifest["entry_point"] = "python -m cropews.demo_evaluation"
    manifest["python"] = sys.version.split()[0]
    stable = json.dumps(_stable(manifest), sort_keys=True)
    manifest["artifact_sha256"] = hashlib.sha256(stable.encode()).hexdigest()
    if args.check:
        expected = json.loads(open(args.check).read())
        if _stable(expected) != _stable(manifest):
            print("MISMATCH vs expected manifest", file=sys.stderr)
            sys.exit(1)
        print("manifest matches expected output")
        return
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
