import yaml
from addresskit.preprocessing.clean_text import normalize_text, extract_parts

cfg = yaml.safe_load(open("configs/normalize.yaml", encoding="utf-8"))

def test_tr_lower_and_expand():
    s,_ = normalize_text("Çamlıca Mh. 5. Sk. No:12 D:3", cfg)
    assert "mahalle" in s and "sokak" in s and "no 12" in s and "daire 3" in s

def test_parts():
    s,_ = normalize_text("Atak mah 123. sokak no:7 kat 2 daire 5", cfg)
    parts = extract_parts(s, cfg)
    assert parts["no"] == "7"
    assert parts["kat"] == "2"
    assert parts["daire"] == "5"
