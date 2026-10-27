import numpy as np
import pandas as pd
import pytest

from cropews.data.yields import parse_district_yields, yield_anomaly

SAMPLE = """Tabelle: 41241-03i
;;;Fruchtarten;Fruchtarten
;;;Weizen zusammen;Winterweizen
;;;dt/ha;dt/ha
2023;05;Nordrhein-Westfalen;81,8;82,2
2023;059;  Arnsberg, Regierungsbezirk;80,0;80,5
2023;05974;    Soest, Kreis;87,0;87,4
2023;05362;    Rhein-Erft-Kreis;84,0;.
2024;05974;    Soest, Kreis;73,8;75,4
"""


def test_parse_keeps_districts_converts_units_and_missing():
    y = parse_district_yields(SAMPLE)
    assert y["ags"].tolist() == ["05974", "05362", "05974"]
    assert y["district"].tolist() == ["Soest", "Rhein-Erft-Kreis", "Soest"]
    assert y["yield_t_ha"].iloc[0] == pytest.approx(8.74)
    assert np.isnan(y["yield_t_ha"].iloc[1])


def test_parse_reads_latin1_file(tmp_path):
    path = tmp_path / "t.csv"
    path.write_bytes(SAMPLE.replace("Soest", "Höxter").encode("latin-1"))
    assert parse_district_yields(path)["district"].iloc[0] == "Höxter"


def test_anomaly_is_against_other_years_of_same_district():
    y = pd.DataFrame(
        {"year": [1, 2, 3, 1], "ags": ["a", "a", "a", "b"], "yield_t_ha": [8.0, 8.0, 6.0, 5.0]}
    )
    a = yield_anomaly(y)["yield_anomaly"]
    assert a.iloc[2] == pytest.approx(6 / 8 - 1)
    assert a.iloc[0] == pytest.approx(8 / 7 - 1)
    assert np.isnan(a.iloc[3])  # single year: no reference


def test_anomaly_ignores_missing_years_in_reference():
    y = pd.DataFrame({"year": [1, 2, 3], "ags": ["a", "a", "a"], "yield_t_ha": [8.0, np.nan, 6.0]})
    a = yield_anomaly(y)["yield_anomaly"]
    assert a.iloc[0] == pytest.approx(8 / 6 - 1)
    assert np.isnan(a.iloc[1])
