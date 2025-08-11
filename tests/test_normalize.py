# -*- coding: utf-8 -*-
from pathlib import Path
from addresskit.normalize import normalize_address

def test_normalize_address(tmp_path: Path):
    src = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    cfg = tmp_path / "cfg.yaml"

    # İSTANBUL   BaĞcılar
    src.write_text("address\n\u0130STANBUL   Ba\u011Fc\u0131lar\n", encoding="utf-8")
    cfg.write_text("lowercase: true\nstrip_extra_spaces: true\n", encoding="utf-8")

    normalize_address(str(src), str(out), str(cfg))
    text = out.read_text(encoding="utf-8")
    assert "istanbul ba\u011Fc\u0131lar" in text
