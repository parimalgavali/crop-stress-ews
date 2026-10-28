from datetime import date

from cropews.data.phenology import crop_start, nearby_stage, parse_observations, parse_stations

OBS = """Stations_id;Referenzjahr;Qualitaetsniveau;Objekt_id;Phase_id;Eintrittsdatum;QB;Jultag;eor;
        1;   2026;  1;  202;  24;  20260804;  1;  216;eor;
        1;   2026;  1;  202;  10;  20261002;  1;  275;eor;
        1;   2026;  1;  202;  12;  20261011;  1;  284;eor;
        2;   2026;  1;  202;  10;  20261005;  1;  278;eor;
        2;   2026;  1;  202;  12;  20261020;  1;  293;eor;
        3;   2026;  1;  202;  10;  20261010;  1;  283;eor;
        3;   2026;  1;  202;  12;  20261030;  1;  303;eor;
        9;   2026;  1;  202;  12;  20261001;  1;  274;eor;
"""
STATIONS = """Stations_id;Stationsname;geograph.Breite;geograph.Laenge;Hoehe;Bundesland;eor;
00001 ;Near A ; 51.50 ; 8.00 ; 90 ;Nordrhein-Westfalen;eor;
00002 ;Near B ; 51.60 ; 8.10 ; 90 ;Nordrhein-Westfalen;eor;
00003 ;Near C ; 51.40 ; 7.90 ; 90 ;Nordrhein-Westfalen;eor;
00009 ;Far    ; 53.50 ; 10.0 ; 10 ;Hamburg;eor;
"""


def test_nearby_stage_needs_half_of_the_observers_and_ignores_the_previous_crop_and_far_ones():
    obs, st = parse_observations(OBS), parse_stations(STATIONS)
    assert list(st["name"]) == ["Near A", "Near B", "Near C", "Far"]
    # 25 Oct: A and B emerged, C only sown -> 2 of 3 emerged; the August harvest is last crop's
    out = nearby_stage(obs, st, 51.5, 8.0, date(2026, 10, 25))
    assert out == {
        "stage": "emerged",
        "observers": 3,
        "at_stage": 2,
        "first_date": "2026-10-11",
        "radius_km": 40,
    }
    # 15 Oct: only A emerged -> 1 of 3 is below half, so the stage is "sown" (all 3)
    early = nearby_stage(obs, st, 51.5, 8.0, date(2026, 10, 15))
    assert early is not None and early["stage"] == "sown" and early["at_stage"] == 3
    assert nearby_stage(obs, st, 48.0, 11.0, date(2026, 10, 25)) is None


def test_crop_start_is_the_sowing_september():
    assert crop_start(date(2026, 10, 28)) == date(2026, 9, 1)
    assert crop_start(date(2027, 5, 1)) == date(2026, 9, 1)
