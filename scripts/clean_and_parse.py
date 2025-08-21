# -*- coding: utf-8 -*-
"""
Türkçe adres temizleme + normalizasyon + parça çıkarımı
- Boş/çok kısa/anlamsız adresler atılır
- Satır içi newline (\r?\n) normalize edilir
- Eksik/NaN değerler normalize edilir
- Tam satır dup'ları ve address_clean dup'ları düşürülür
- Şüpheli satırlar opsiyonel olarak atılabilir veya ayrı dosyaya yazılır
"""

import os
import re
import unicodedata
import pandas as pd
from typing import Dict, Tuple

# ---------------- I/O ----------------
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # repo kökü
RAW_DIR  = os.path.join(ROOT_DIR, "data", "raw")
OUT_DIR  = os.path.join(ROOT_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

TRAIN_IN  = os.path.join(RAW_DIR, "train.csv")
TEST_IN   = os.path.join(RAW_DIR, "test.csv")
TRAIN_OUT = os.path.join(OUT_DIR, "train_clean_parsed.csv")
TEST_OUT  = os.path.join(OUT_DIR, "test_clean_parsed.csv")

# ---------------- Regex Yardımcıları ----------------
MULTISPACE_RE = re.compile(r"\s+")
SAFE_CHARS_RE = re.compile(r"[^0-9a-zçğıöşü\s./\-]", flags=re.IGNORECASE)
COLON_RE      = re.compile(r"\s*[:;|]\s*")
ONLY_PUNCT_SP_RE = re.compile(r"^[\s\W_]+$")  # sadece boşluk/noktalama

def tr_lower(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("İ", "i").replace("I", "ı")
    s = unicodedata.normalize("NFKC", s).lower().replace("\u0307", "")
    return s

def norm_spaces(s: str) -> str:
    return MULTISPACE_RE.sub(" ", s).strip()

def strip_punct_but_keep_address_separators(s: str) -> str:
    s = re.sub(r"(?<=\D)[\.,](?=\D)", " ", s)
    s = re.sub(r"(?<=\D)[\.,](?=\d)", " ", s)
    s = re.sub(r"(?<=\d)[,](?=\D)", " ", s)
    s = re.sub(r"[(){}\[\]!?]+", " ", s)
    s = COLON_RE.sub(" ", s)
    s = SAFE_CHARS_RE.sub(" ", s)
    return s

# ---------- Kısaltma / normalizasyon ---------- #
CANONICAL_SUBS = [
    (r"\bmahallesi\b", "mahalle"),
    (r"\bmah\b", "mahalle"),
    (r"\bmh\b", "mahalle"),
    (r"\bmhl\b", "mahalle"),
    (r"\bmah.\b", "mahalle"),
    (r"\bmh.\b", "mahalle"),
    (r"\bmahalle\b", "mahalle"),
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
    (r"\bd\b(?=\s*\d)", "daire"),
    (r"\bdaire\b", "daire"),
    (r"\bk\b(?=\s*\d)", "kat"),
    (r"\bapt\b", "apartman"),
    (r"\bap\b", "apartman"),
    (r"\bblv\b", "bulvar"),
]

NO_FIX_RE    = re.compile(r"\bno\s*([0-9]+[a-z]?(?:/[0-9a-z]+)?)\b", re.IGNORECASE)
KAT_FIX_RE   = re.compile(r"\bkat\s*([0-9]+[a-z]?)\b", re.IGNORECASE)
DAIRE_FIX_RE = re.compile(r"\bdaire\s*([0-9]+[a-z]?)\b", re.IGNORECASE)

def normalize_address(raw: str) -> str:
    s = tr_lower(raw)
    s = re.sub(r"\r?\n", " ", s)                   # 🔹 newline normalize
    s = strip_punct_but_keep_address_separators(s)
    s = re.sub(r"(\d+)\.(sokak|cadde|mahalle)\b", r"\1 \2", s)
    s = re.sub(r"(?<!\d)/(?!\d)", " / ", s)
    for pat, repl in CANONICAL_SUBS:
        s = re.sub(pat, repl, s)
    s = NO_FIX_RE.sub(r"no \1", s)
    s = KAT_FIX_RE.sub(r"kat \1", s)
    s = DAIRE_FIX_RE.sub(r"daire \1", s)
    return norm_spaces(s)

# ---------------- Parça çıkarımı ----------------
RE_NO      = re.compile(r"\bno\s*([0-9]+[a-z]?(?:/[0-9a-z]+)?)\b")
RE_DAIRE   = re.compile(r"\bdaire\s*([0-9a-z]+)\b")
RE_KAT     = re.compile(r"\bkat\s*([0-9a-z]+)\b")
RE_NUM_SOK = re.compile(r"\b(\d+)\s+sokak\b")

ANCHOR_STOP = r"(?:mahalle|cadde|sokak|bulvar|no|daire|kat|mevkii|apartman|hotel|otel|plaza|blok|işhanı|iş hanı|bina|site|sitesi|residence|rezidans|$)"
def extract_following_name(text: str, anchor: str) -> str:
    pat = rf"{anchor}\s+([a-zğüşiöç0-9 \-]+?)\s+(?={ANCHOR_STOP})"
    m = re.search(pat, text)
    if m:
        val = norm_spaces(m.group(1))
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

    mah = extract_following_name(txt, "mahalle")
    if mah: parts["mahalle"] = mah

    cad = extract_following_name(txt, "cadde")
    if cad: parts["cadde"] = cad

    m = RE_NUM_SOK.search(txt)
    if m:
        parts["sokak"] = m.group(1)
    else:
        sok = extract_following_name(txt, "sokak")
        if sok: parts["sokak"] = sok

    m = re.search(r"\b([a-zğüşiöç\-]+)\s+mevkii\b", txt)
    if m:
        parts["mevkii"] = m.group(1)

    m = re.search(r"\b(apartman|residence|rezidans|blok|işhanı|iş hanı|plaza|hotel|otel|site|sitesi|bina)\b", txt)
    if m:
        trigger = m.group(1)
        left = re.findall(r"[a-zğüşiöç\-]+", txt[:m.start()])
        name = " ".join(left[-2:] + [trigger]).strip()
        name = re.sub(r"^(no\s*\d+[a-z]?/?\d*\s*)", "", name).strip()
        name = re.sub(r"^\d+[a-z]?\s*", "", name).strip()
        if name:
            parts["bina_adi"] = name

    parts.update(guess_city_district(txt))

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

# -------------- Çekirdek temizleme --------------
PART_COLS = ["mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce","_confidence"]

def process_file(
    in_path: str,
    out_path: str,
    has_label: bool,
    add_missing_id: bool = True,
    drop_exact_duplicates: bool = True,
    drop_clean_duplicates: bool = True,
    drop_suspicious: bool = False
):
    print(f"[RUN] reading: {os.path.abspath(in_path)}")
    # Daha sağlam CSV okuma
    df = pd.read_csv(in_path, encoding="utf-8", engine="python", on_bad_lines="skip")

    # --- global string temizlik: \r?\n -> ' ', strip ---
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.replace(r"\r?\n", " ", regex=True).str.strip()

    # --- 'address' mecburi ve anlamlı olsun ---
    if "address" not in df.columns:
        df.columns = [c.lower() for c in df.columns]
    if "address" not in df.columns:
        raise ValueError("Girdi dosyasında 'address' kolonu yok.")

    df = df[df["address"].notna()]
    df = df[df["address"].str.strip() != ""]
    df = df[~df["address"].str.match(ONLY_PUNCT_SP_RE)]     # sadece noktalama/boşluk olanları at
    df = df[df["address"].str.len() > 5]                    # çok kısa olanları at

    # --- normalize + parse ---
    parsed = df["address"].map(normalize_and_parse)
    df["address_clean"] = parsed.map(lambda x: x[0])
    parts_series = parsed.map(lambda x: x[1])

    for k in PART_COLS:
        df[k] = parts_series.map(lambda d, kk=k: d.get(kk, ""))

    # --- eksik/NaN normalize ---
    df = df.fillna("")  # tüm NaN'ları boş string yap (metin modeli için güvenli)

    # --- kalite bayrakları ---
    df = add_quality_flags(df, "address_clean")

    # --- tam satır dup'ları düşür ---
    if drop_exact_duplicates:
        before = len(df)
        df = df.drop_duplicates()
        print(f"[INFO] Exact-duplicate rows dropped: {before - len(df)}")

    # --- address_clean bazlı dup'ları düşür ---
    if drop_clean_duplicates:
        before = len(df)
        df = df.drop_duplicates(subset=["address_clean"])
        print(f"[INFO] address_clean-duplicate rows dropped: {before - len(df)}")

    # --- ID ekle (gerekirse) ---
    if add_missing_id and "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))

    # --- şüphelileri işleme ---
    susp = df[df["is_suspicious"] == 1]
    if not susp.empty:
        susp_path = out_path.replace(".csv", "_suspicious.csv")
        susp.to_csv(susp_path, index=False, encoding="utf-8-sig")
        print(f"[INFO] Suspicious saved: {os.path.abspath(susp_path)} (rows={len(susp)})")
        if drop_suspicious:
            df = df[df["is_suspicious"] == 0]
            print(f"[INFO] Suspicious rows removed from main set.")

    # --- kolon sırası ---
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

    # --- kaydet ---
    print(f"[RUN] writing: {os.path.abspath(out_path)} (rows={len(df)})")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

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
