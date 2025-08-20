# -*- coding: utf-8 -*-
"""
Türkçe adres normalizasyonu + parça çıkarımı (mah, cad, sok, no, daire, kat, bina_adı, mevkii, il/ilçe)
Heuristik + regex tabanlı. Çıktıya _confidence ekler.
"""
import re
import unicodedata
from typing import Dict, Tuple

# yaygın kısaltmaların açılımları (dikkat: 'd' sadece d: / d. olarak genişletilir)
ABBR = {
    r"\bmah\.?\b": "mahalle",
    r"\bmahallesi\b": "mahalle",
    r"\bmh\.?\b": "mahalle",
    r"\bcad\.?\b": "cadde",
    r"\bcaddesi\b": "cadde",
    r"\bcd\.?\b": "cadde",
    r"\bsok\.?\b": "sokak",
    r"\bsokağı\b": "sokak",
    r"\bsk\.?\b": "sokak",
    r"\bbulv?\.?\b": "bulvar",
    r"\bbulvarı\b": "bulvar",
    r"\bno:?": "no ",
    r"\bkapı no:?": "no ",
    r"\bd[.:]\b": "daire ",
    r"\bdaire:?": "daire ",
    r"\bk:?": "kat ",
    r"\bkat:?": "kat ",
    r"\bapt\.?\b": "apartman",
    r"\bap\b": "apartman",
    r"\bmevkii\b": "mevkii",
}

CITY_HINTS = {
    "istanbul","ankara","izmir","bursa","antalya","muğla","aydın","tekirdağ","kocaeli",
    "konya","adana","mersin","samsun","eskişehir","trabzon","kayseri","gaziantep"
}
DISTRICT_HINTS = {
    "fethiye","çeşme","bodrum","kartal","kadıköy","üsküdar","ataşehir","bornova",
    "konak","mamak","keçiören","tepebaşı","odunpazarı","tarsus","tekkeköy"
}

def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _strip_punct_but_keep_separators(text: str) -> str:
    # kelime içi 10/3 vb. kalsın; virgül/nokta çoğunlukla boşluk olsun
    text = re.sub(r"(?<=\D)[\.,](?=\D)", " ", text)
    text = re.sub(r"(?<=\D)[\.,](?=\d)", " ", text)
    text = re.sub(r"(?<=\d)[,](?=\D)", " ", text)
    text = re.sub(r"[;:|]+", " ", text)
    return text

def clean_text(s: str) -> str:
    # None/NaN koruması + TR-safe lower
    if s is None: s = ""
    s = str(s).replace("İ", "i").replace("I", "ı")
    s = unicodedata.normalize("NFKC", s).lower().replace("\u0307", "")

    s = _strip_punct_but_keep_separators(s)

    for pat, repl in ABBR.items():
        s = re.sub(pat, repl, s)

    # 'd 1' → 'daire 1' (yalnız d + sayı; "doria" etkilenmez)
    s = re.sub(r"\bd\s+(?=\d)", "daire ", s)
    # güvenlik: no:15 / no15 → no 15
    s = re.sub(r"\bno\s*[:\-]?\s*(\d+)", r"no \1", s)

    # 864.sokak → 864 sokak vb.
    s = re.sub(r"(\d+)\.(sokak|cadde|mahalle)\b", r"\1 \2", s)

    # sayi/harf ve slash'lı daireleri koru; diğer slash etrafına boşluk
    s = re.sub(r"(?<!\d)/(?!\d)", " / ", s)

    s = _normalize_spaces(s)
    return s

# desenler
RE_NO      = re.compile(r"\bno\s*([0-9]+[a-z]?(?:/[0-9a-z]+)?)\b")
RE_DAIRE   = re.compile(r"\bdaire\s*([0-9a-z]+)\b")
RE_KAT     = re.compile(r"\bkat\s*([0-9a-z]+)\b")
RE_NUM_SOK = re.compile(r"\b(\d+)\s+sokak\b", re.IGNORECASE)

def _extract_following_name(text: str, anchor: str) -> str:
    pat = rf"{anchor}\s+([a-zğüşiöç0-9 \-]+?)\s+(?=(mahalle|cadde|sokak|bulvar|no|daire|kat|mevkii|apartman|hotel|otel|plaza|blok|işhanı|iş hanı|$))"
    m = re.search(pat, text)
    return _normalize_spaces(m.group(1)) if m else ""

def _guess_city_district(text: str) -> Dict[str, str]:
    il = ilce = ""
    pieces = [ _normalize_spaces(x) for x in re.split(r"/", text) ]
    for p in reversed(pieces):
        toks = set(p.split())
        if not il and toks & CITY_HINTS:   il   = list(toks & CITY_HINTS)[0]
        if not ilce and toks & DISTRICT_HINTS: ilce = list(toks & DISTRICT_HINTS)[0]
    out = {}
    if il: out["il"] = il
    if ilce: out["ilçe"] = ilce
    return out

def normalize_and_parse(raw) -> Tuple[str, Dict[str, str]]:
    if raw is None: raw = ""
    txt = clean_text(str(raw))
    parts: Dict[str, str] = {}

    # numaralı alanlar
    m = RE_NO.search(txt)
    if m:
        parts["no"] = m.group(1).strip()
        if "/" in parts["no"]:
            n, d = parts["no"].split("/", 1)
            if n.isdigit() and d.isdigit():
                parts["no"], parts["daire"] = n, d

    m = RE_DAIRE.search(txt)
    if m and re.fullmatch(r"\d+[a-z]?", m.group(1)):
        parts.setdefault("daire", m.group(1).strip())

    m = RE_KAT.search(txt)
    if m and re.fullmatch(r"\d+[a-z]?", m.group(1)):
        parts["kat"] = m.group(1).strip()

    # isimli alanlar
    mah = _extract_following_name(txt, "mahalle")
    if mah: parts["mahalle"] = mah
    cad = _extract_following_name(txt, "cadde")
    if cad: parts["cadde"] = cad

    # sokak: sayısal ada öncelik
    m = RE_NUM_SOK.search(txt)
    if m:
        parts["sokak"] = m.group(1)
    else:
        sok = _extract_following_name(txt, "sokak")
        if sok: parts["sokak"] = sok

    # mevkii / bina_adı (basit)
    m = re.search(r"\b([a-zğüşiöç\-]+)\s+mevkii\b", txt)
    if m:
        parts["mevkii"] = m.group(1)

    m = re.search(r"\b(apartman|residence|rezidans|blok|işhanı|iş hanı|plaza|hotel|otel)\b", txt)
    if m:
        trigger = m.group(1)
        left = re.findall(r"[a-zğüşiöç\-]+", txt[:m.start()])
        name = " ".join(left[-2:] + [trigger]).strip()
        # başta 'no/sayı' kirlerini temizle
        name = re.sub(r"^\bno\b\s*\d+[a-z]?\/?\d*\s*", "", name).strip()
        name = re.sub(r"^\d+[a-z]?\s*", "", name).strip()
        if name:
            parts["bina_adı"] = name

    # il / ilçe tahmini
    parts.update(_guess_city_district(txt))

    # normalized string (gösterim)
    normalized = _normalize_spaces(txt)

    # basit güven skoru
    keys = {"mahalle","cadde","sokak","no","daire","kat","bina_adı","mevkii","il","ilçe"}
    found = [k for k in parts.keys() if k in keys]
    score = 0.2 * len(found)
    if "no" in parts: score += 0.2
    if any(k in parts for k in ("mahalle","cadde","sokak")): score += 0.2
    parts["_confidence"] = round(max(0.0, min(1.0, score)), 2)

    return normalized, parts
