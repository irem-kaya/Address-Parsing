from pathlib import Path
from addresskit.match import match_addresses
import csv


def test_match(tmp_path: Path):
    left = tmp_path / "left.csv"
    right = tmp_path / "right.csv"
    out = tmp_path / "out.csv"
    cfg = tmp_path / "cfg.yaml"

    left.write_text("id,address\n0,A Sokak 1\n1,B Cadde 2\n", encoding="utf-8")
    right.write_text("id,address\n0,A Street 1\n1,B Avenue 2\n", encoding="utf-8")
    cfg.write_text("method: index\nthreshold: 0.8\n", encoding="utf-8")

    match_addresses(str(left), str(right), str(out), str(cfg))

    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == 2
    assert (
        rows[0]["left_id"] == "0"
        and rows[0]["right_id"] == "0"
        and float(rows[0]["score"]) == 1.0
    )
    assert (
        rows[1]["left_id"] == "1"
        and rows[1]["right_id"] == "1"
        and float(rows[1]["score"]) == 1.0
    )
