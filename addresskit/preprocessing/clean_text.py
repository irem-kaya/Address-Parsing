# -*- coding: utf-8 -*-
"""
Türkçe adres temizleme + normalizasyon + parça çıkarımı (mah,cad,sok,no,daire,kat,bina_adi,mevkii,il,ilce)
- EDA bulgularına göre: kısaltmalar, noktalama/colon, 864.sok → 864 sokak, slash mantığı, TR-safe lower
- Çıktılar: address_clean, parçalar, _confidence, kalite bayrakları
- Train/test üzerinde çalışır ve data/processed altına yazar.
"""

import os
import re
import unicodedata
from typing import Dict, Tuple, Optional
import pandas as pd

# ---------------- I/O ----------------
RAW_DIR = os.path.join("data", "raw")
OUT_DIR = os.path.join("data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

TRAIN_IN  = os.path.join(RAW_DIR, "train.csv")
TEST_IN   = os.path.join(RAW_DIR, "test.csv")
TRAIN_OUT = os.path.join(OUT_DIR, "train_clean_parsed.csv")
TEST_OUT  = os.path.join(OUT_DIR, "test_clean_parsed.csv")

# ---------------- Yardımcılar ----------------
MULTISPACE_RE = re.compile(r"\s+")
# EDA: ./- işimize yarıyor; diğerlerini temizleyeceğiz
SAFE_CHARS_RE = re.compile(r"[^0-9a-zçğıöşü\s./\-]", flags=re.IGNORECASE)
COLON_RE = re.compile(r"\s*[:;|]\s*")  # no:10, d:3, kat:2 varyasyonları

def tr_lower(s: str) -> str:
    # Türkçe güvenli lower + noktalama normalizasyonu
    if s is None:
        return ""
    s = str(s)
    s = s.replace("İ", "i").replace("I", "ı")
    s = unicodedata.normalize("NFKC", s).lower().replace("\u0307", "")
    return s

def norm_spaces(s: str) -> str:
    return MULTISPACE_RE.sub(" ", s).strip()

def strip_punct_but_keep_address_separators(s: str) -> str:
    # “no:10/3, d:5.” gibi kalıplarda ./- kalsın, diğer anlamsızlar boşluk olsun
    # virgül ve nokta çoğu zaman ayırıcı; sayılar arasında değilse boşluk yap
    s = re.sub(r"(?<=\D)[\.,](?=\D)", " ", s)
    s = re.sub(r"(?<=\D)[\.,](?=\d)", " ", s)
    s = re.sub(r"(?<=\d)[,](?=\D)", " ", s)
    s = re.sub(r"[(){}\[\]!?]+", " ", s)
    s = COLON_RE.sub(" ", s)  # ':' → boşluk
    s = SAFE_CHARS_RE.sub(" ", s)
    return s

# ---------- Kısaltma/normalizasyon eşlemeleri ----------
# EDA: mah/mh; cad/cd/caddesi; sok/sk/sokağı; no/no./numara; d: → daire; blv → bulvar, apt/ap
CANONICAL_SUBS = [
    (r"\bmahallesi\b", "mahalle"),
    (r"\bmah\b", "mahalle"),
    (r"\bmh\b", "mahalle"),
    (r"\bmhl\b", "mahalle"),
    (r"\bcaddesi\b", "cadde"),
    (r"\bcad\b", "cadde"),
    (r"\bcd\b", "cadde"),
    (r"\bsokağı\b", "sokak"),
    (r"\bsokagi\b", "sokak"),
    (r"\bsok\b", "sokak"),
    (r"\bsk\b", "sokak"),
    (r"\bbulv?\b", "bulvar"),
    (r"\bbulvarı\b", "bulvar"),
    (r"\bno\.?\b", "no"),
    (r"\bnumara\b", "no"),
    (r"\bkapı\s*no\b", "no"),
    (r"\bd[.]\b", "daire"),
    (r"\bd\b(?=\s*\d)", "daire"),  # sadece d + sayı
    (r"\bdaire\b", "daire"),
    (r"\bk\b(?=\s*\d)", "kat"),
    (r"\bapt\b", "apartman"),
    (r"\bap\b", "apartman"),
    (r"\bblv\b", "bulvar"),
]

NO_FIX_RE     = re.compile(r"\bno\s*([0-9]+[a-z]?(?:/[0-9a-z]+)?)\b", re.IGNORECASE)
KAT_FIX_RE    = re.compile(r"\bkat\s*([0-9]+[a-z]?)\b", re.IGNORECASE)
DAIRE_FIX_RE  = re.compile(r"\bdaire\s*([0-9]+[a-z]?)\b", re.IGNORECASE)

def normalize_address(raw: str) -> str:
    s = tr_lower(raw)
    s = strip_punct_but_keep_address_separators(s)

    # 864.sokak → 864 sokak (cadde/mahalle de)
    s = re.sub(r"(\d+)\.(sokak|cadde|mahalle)\b", r"\1 \2", s)

    # slash: sayı/sayı (no/daire gibi) kalsın; diğer slash çevresine boşluk
    s = re.sub(r"(?<!\d)/(?!\d)", " / ", s)

    # kısaltmaları aç
    for pat, repl in CANONICAL_SUBS:
        s = re.sub(pat, repl, s)

    # biçim sabitleme
    s = NO_FIX_RE.sub(r"no \1", s)
    s = KAT_FIX_RE.sub(r"kat \1", s)
    s = DAIRE_FIX_RE.sub(r"daire \1", s)

    s = norm_spaces(s)
    return s

# ---------------- Parça çıkarımı ----------------
RE_NO       = re.compile(r"\bno\s*([0-9]+[a-z]?(?:/[0-9a-z]+)?)\b")
RE_DAIRE    = re.compile(r"\bdaire\s*([0-9a-z]+)\b")
RE_KAT      = re.compile(r"\bkat\s*([0-9a-z]+)\b")
RE_NUM_SOK  = re.compile(r"\b(\d+)\s+sokak\b")

# Şablon: 'anchor' kelimesinden sonra gelen isim, bir sonraki anchor'a kadar
ANCHOR_STOP = r"(?:mahalle|cadde|sokak|bulvar|no|daire|kat|mevkii|apartman|hotel|otel|plaza|blok|işhanı|iş hanı|bina|site|sitesi|residence|rezidans|$)"
def extract_following_name(text: str, anchor: str) -> str:
    pat = rf"{anchor}\s+([a-zğüşiöç0-9 \-]+?)\s+(?={ANCHOR_STOP})"
    m = re.search(pat, text)
    if m:
        val = norm_spaces(m.group(1))
        # Başta/sonda kalan gereksiz numara/no gibi kirleri temizle
        val = re.sub(r"^(no\s*\d+[a-z]?(?:/\d+)?)\b", "", val).strip()
        return val
    return ""

CITY_HINTS = {
    "istanbul","ankara","izmir","bursa","antalya","muğla","aydın","tekirdağ","kocaeli","konya",
    "adana","mersin","samsun","eskişehir","trabzon","kayseri","gaziantep","balıkesir","manisa",
    "şanlıurfa","diyarbakır","hatay","k.maraş","kahramanmaraş","denizli","sakarya","tekirdag"
}
DISTRICT_HINTS = {
    "fethiye","çeşme","bodrum","kartal","kadıköy","üsküdar","ataşehir","bornova","konak","mamak",
    "keçiören","tepebaşı","odunpazarı","tarsus","tekkeköy","buca","karabağlar","karşıyaka","menemen",
    "bayrakli","bayraklı","çamlıyayla","muratpaşa","kepez","seyhan","yüreğir","çankaya","yenimahalle"
}

def guess_city_district(text: str) -> Dict[str, str]:
    il = ilce = ""
    # '... ilçe/il' gibi son parçalardan tarama
    pieces = [norm_spaces(x) for x in re.split(r"/", text)]
    for p in reversed(pieces):
        toks = set(p.split())
        if not il and (toks & CITY_HINTS):
            il = list(toks & CITY_HINTS)[0]
        if not ilce and (toks & DISTRICT_HINTS):
            ilce = list(toks & DISTRICT_HINTS)[0]
    out = {}
    if il: out["il"] = il
    if ilce: out["ilce"] = ilce
    return out

def normalize_and_parse(raw: str) -> Tuple[str, Dict[str, str]]:
    txt = normalize_address(raw)
    parts: Dict[str, str] = {}

    # sayısal alanlar
    m = RE_NO.search(txt)
    if m:
        parts["no"] = m.group(1).strip()
        # no 10/3 → daire 3
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
    mah = extract_following_name(txt, "mahalle")
    if mah: parts["mahalle"] = mah

    cad = extract_following_name(txt, "cadde")
    if cad: parts["cadde"] = cad

    # sokak (önce sayı/sokak deseni)
    m = RE_NUM_SOK.search(txt)
    if m:
        parts["sokak"] = m.group(1)
    else:
        sok = extract_following_name(txt, "sokak")
        if sok: parts["sokak"] = sok

    # mevkii / bina_adi (basit çıkarım)
    m = re.search(r"\b([a-zğüşiöç\-]+)\s+mevkii\b", txt)
    if m:
        parts["mevkii"] = m.group(1)

    m = re.search(r"\b(apartman|residence|rezidans|blok|işhanı|iş hanı|plaza|hotel|otel|site|sitesi|bina)\b", txt)
    if m:
        trigger = m.group(1)
        left = re.findall(r"[a-zğüşiöç\-]+", txt[:m.start()])
        name = " ".join(left[-2:] + [trigger]).strip()
        # baştaki sayı/no kirleri
        name = re.sub(r"^(no\s*\d+[a-z]?/?\d*\s*)", "", name).strip()
        name = re.sub(r"^\d+[a-z]?\s*", "", name).strip()
        if name:
            parts["bina_adi"] = name

    # il/ilçe tahmini
    parts.update(guess_city_district(txt))

    # güven skoru
    keys = {"mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce"}
    score = 0.0
    found = [k for k in parts if k in keys]
    score += 0.15 * len(found)
    if "no" in parts: score += 0.15
    if any(k in parts for k in ("mahalle","cadde","sokak")): score += 0.2
    score = max(0.0, min(1.0, score))
    parts["_confidence"] = round(score, 2)

    return txt, parts

# -------------- Kalite metrikleri --------------
def add_quality_flags(df: pd.DataFrame, col: str) -> pd.DataFrame:
    s = df[col].astype(str)
    df["char_len"]    = s.str.len()
    df["word_len"]    = s.str.split().map(len)
    df["digit_count"] = s.str.count(r"\d")
    df["punct_count"] = s.str.count(r"[^\w\s]")
    df["is_suspicious"] = (
        (df["char_len"] < 10) |
        (df["word_len"] < 2)  |
        (df["char_len"] > 180)|
        (df["digit_count"] == 0)
    ).astype(int)
    df["is_duplicate_clean"] = df.duplicated(subset=[col], keep=False).astype(int)
    return df

# -------------- İşleyici --------------
PART_COLS = ["mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce","_confidence"]

def process_file(in_path: str, out_path: str, has_label: bool):
    print(f"[RUN] reading: {os.path.abspath(in_path)}")
    df = pd.read_csv(in_path)
    if "address" not in df.columns:
        df.columns = [c.lower() for c in df.columns]
        if "address" not in df.columns:
            raise ValueError("Girdi dosyasında 'address' kolonu yok.")

    # normalize + parse
    parsed = df["address"].astype(str).map(normalize_and_parse)
    df["address_clean"] = parsed.map(lambda x: x[0])
    parts_series = parsed.map(lambda x: x[1])

    # bileşen kolonları
    for k in PART_COLS:
        df[k] = parts_series.map(lambda d: d.get(k, ""))

    # kalite bayrakları
    df = add_quality_flags(df, "address_clean")

    # kolon sırası
    base_cols = ["address","address_clean"] + PART_COLS + [
        "char_len","word_len","digit_count","punct_count",
        "is_suspicious","is_duplicate_clean"
    ]
    cols = []
    if "id" in df.columns: cols.append("id")
    cols += base_cols
    if has_label and "label" in df.columns: cols.append("label")
    cols = [c for c in cols if c in df.columns]

    df = df[cols]
    print(f"[RUN] writing: {os.path.abspath(out_path)} (rows={len(df)})")
    df.to_csv(out_path, index=False)

def main():
    if os.path.exists(TRAIN_IN):
        process_file(TRAIN_IN, TRAIN_OUT, has_label=True)
    else:
        print(f"[WARN] Train bulunamadı: {TRAIN_IN}")

    if os.path.exists(TEST_IN):
        process_file(TEST_IN, TEST_OUT, has_label=False)
    else:
        print(f"[INFO] Test bulunamadı (atlandı): {TEST_IN}")

if __name__ == "__main__":
    main()
