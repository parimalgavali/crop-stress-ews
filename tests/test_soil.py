from cropews.data.soil import parse_feature


def test_parse_feature_reads_german_decimals_and_levels():
    props = {"TYP_TEXT": "Gley", "LUFA_TXT": "schluffiger Lehm", "NFK": "216,3", "GW_STUFE": "3"}
    assert parse_feature(props | {"SW_STUFE": "0"}) == {
        "soil_type": "Gley",
        "texture": "schluffiger Lehm",
        "nfk_mm": 216.3,
        "gw_level": 3.0,
        "sw_level": 0.0,
    }
    assert parse_feature({"NFK": "xxx"})["nfk_mm"] is None
