"""Compare stress-event rates per district-season with IT.NRW winter-wheat yield anomalies.

Run scripts/build_labels.py for each district first (it writes events_{district}.parquet).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cropews.config import CORE_DISTRICTS, SEASONS
from cropews.data.yields import parse_district_yields, yield_anomaly
from cropews.sanity import event_rates, rate_yield_correlation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--yields", type=Path, default=Path("data/raw/yields/41241-03i_00.csv"))
    parser.add_argument(
        "--districts", type=Path, default=Path("data/raw/vg2500/vg2500/VG2500_KRS.shp")
    )
    parser.add_argument("--figure", type=Path, default=Path("docs/figures/label_sanity_map.png"))
    args = parser.parse_args()

    fields, events = [], []
    for district in CORE_DISTRICTS:
        ev = args.processed_dir / f"events_{district}.parquet"
        s2_files = sorted((args.interim_dir / "s2").glob(f"s2_{district}_*.parquet"))
        if not ev.exists() or not s2_files:
            print(f"skip {district}: no events or Sentinel-2 files")
            continue
        events.append(pd.read_parquet(ev))
        for f in s2_files:
            ids = pd.read_parquet(f, columns=["field_id", "year"]).drop_duplicates()
            fields.append(ids.assign(district=district))
    rates = event_rates(pd.concat(fields), pd.concat(events))

    kreise = gpd.read_file(args.districts)
    kreise = kreise[kreise["AGS"].str.startswith("05")]
    ags = kreise.set_index("GEN")["AGS"]
    yields = yield_anomaly(parse_district_yields(args.yields))
    yields = yields[yields["year"].isin(SEASONS)].drop(columns="district")
    table = rates.assign(ags=rates["district"].map(ags)).merge(yields, on=["ags", "year"])

    corr = rate_yield_correlation(table)
    by_year = table.groupby("year")[["share", "yield_anomaly"]].mean()
    print(table.pivot(index="district", columns="year", values="share").round(2).to_string())
    print(by_year.round(3).to_string())
    print(f"Spearman(share, yield anomaly) over district-seasons: {corr}")
    rho_year = by_year["share"].corr(by_year["yield_anomaly"], method="spearman")
    print(f"Spearman over season means: {rho_year:.2f}")

    years = sorted(table["year"].unique())
    fig, axes = plt.subplots(1, len(years), figsize=(2.6 * len(years), 3.2))
    for ax, year in zip(axes, years, strict=True):
        share = table[table["year"] == year].set_index("ags")["share"]
        kreise.boundary.plot(ax=ax, color="0.8", linewidth=0.3)
        sel = kreise[kreise["AGS"].isin(share.index)]
        sel.assign(share=sel["AGS"].map(share)).plot(
            column="share", ax=ax, cmap="Reds", vmin=0, vmax=0.5, edgecolor="0.3", linewidth=0.4
        )
        ax.set_title(str(year))
        ax.set_axis_off()
    fig.suptitle("Share of sampled winter-wheat fields with a stress event (core districts)")
    fig.colorbar(axes[-1].collections[-1], ax=axes, shrink=0.7, label="share of fields")
    args.figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.figure, dpi=120, bbox_inches="tight")
    print(f"wrote {args.figure}")


if __name__ == "__main__":
    main()
