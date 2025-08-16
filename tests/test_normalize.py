import yaml
from addresskit.preprocessing.clean_text import normalize_text, extract_parts
import regex as re

cfg = yaml.safe_load(open("configs/normalize.yaml", encoding="utf-8"))

def test_tr_lower_and_expand():
    s, _ = normalize_text("Çamlıca Mh. 5. Sk. No:12 D:3", cfg)
    assert "mahalle" in s and "sokak" in s and "no 12" in s and "daire 3" in s

def extract_parts(text, cfg):
    parts = {}
    for key, pattern in cfg["parts"].items():
        m = re.search(pattern, text)
        if m:
            parts[key] = m.group(1)  # 👈 her zaman key'i doğru ata
    return parts
