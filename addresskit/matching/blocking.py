# addresskit/matching/blocking.py
from __future__ import annotations
import re
from typing import Dict, List


def _alnum_lower(s: str) -> str:
    s = (s or "").lower()
    return re.sub(r"[^a-z0-9ğüşöçıİ]", "", s)


def _first_digits(s: str) -> str:
    m = re.findall(r"\d+", s or "")
    return m[0] if m else ""


def make_block_key(row: dict, text_col: str, mode: str) -> str:
    """
    mode örnekleri:
      - 'prefix8'           : normalize edilmiş metnin alfasayısal ilk 8 karakteri
      - 'digits+prefix6'    : kapı numarası (ilk rakam grubu) + prefix6
      - 'province+district' : 'il'+'ilce' (veya 'province'+'district') birleşimi
    """
    mode = (mode or "").lower().strip()
    txt = row.get(text_col, "")

    if mode.startswith("prefix"):
        n = int(re.findall(r"\d+", mode)[0])
        return _alnum_lower(txt)[:n]

    if mode.startswith("digits+prefix"):
        n = int(re.findall(r"\d+", mode)[0])
        return f"{_first_digits(txt)}|{_alnum_lower(txt)[:n]}"

    if mode == "province+district":
        # olası alan adları
        candidates = [
            ("il", "ilce"),
            ("province", "district"),
            ("city", "county"),
        ]
        for a, b in candidates:
            va, vb = (row.get(a, "") or "").lower().strip(), (
                row.get(b, "") or ""
            ).lower().strip()
            if va or vb:
                return f"{va}|{vb}"
        # bulamazsa text prefix fallback
        return _alnum_lower(txt)[:8]

    # varsayılan: bloklama yok => tek kova
    return ""


def group_by_block(rows: List[dict], text_col: str, mode: str) -> Dict[str, List[dict]]:
    buckets: Dict[str, List[dict]] = {}
    for r in rows:
        k = make_block_key(r, text_col, mode)
        buckets.setdefault(k, []).append(r)
    return buckets
