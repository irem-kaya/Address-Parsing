# -*- coding: utf-8 -*-
import os
import re
from collections import Counter
import pandas as pd
import numpy as np

# --- Veri yolu tespiti (Windows/macOS/Linux için güvenli) ---
CANDIDATES = [
    "data/raw/train.csv",
    "data/train.csv",
    "train.csv",
    os.path.join(os.path.dirname(__file__), "..", "data", "raw", "train.csv"),
    os.path.join(os.path.dirname(__file__), "..", "data", "train.csv"),
]
DATA_PATH = None
for p in CANDIDATES:
    p = os.path.abspath(p)
    if os.path.exists(p):
        DATA_PATH = p
        break
if DATA_PATH is None:
    raise FileNotFoundError(
        "train.csv bulunamadı. Lütfen dosyayı 'data/raw/train.csv' altına koyun "
        "veya DeepEDA.py içindeki CANDIDATES listesine doğru yolu ekleyin."
)
print(f"[EDA] Kullanılan train yolu: {DATA_PATH}")

# ----------------------------------
# 0) Yollar ve I/O
# ----------------------------------
DATA_PATH = "data/raw/train.csv"   # Senin yüklediğin dosya yolu
OUTDIR = "data/interim/eda_reports"
os.makedirs(OUTDIR, exist_ok=True)

# ----------------------------------
# 1) Veri Yükleme ve Hızlı Şema
# ----------------------------------
df = pd.read_csv(DATA_PATH)
print(">> Shape:", df.shape)
print(">> Columns:", list(df.columns))

print("\n>> dtypes:")
print(df.dtypes)

print("\n>> İlk 5 satır:")
print(df.head(5))

# Beklenen minimum kolonlar (örnek varsayım)
# - id (testte kesin olur; trainde opsiyonel)
# - address (zorunlu metin alanı)
# - label (trainde zorunlu)
cols_lower = [c.lower() for c in df.columns]
has_id = "id" in cols_lower
has_address = "address" in cols_lower
has_label = "label" in cols_lower

if not has_address:
    raise ValueError("Bu EDA adımı 'address' sütunu olmadan çalışmaz. Lütfen 'address' sütunu olduğundan emin ol.")

# Kolon adlarını normalize et (küçük harfe indir)
df.columns = [c.lower() for c in df.columns]

# ----------------------------------
# 2) Eksik Değer Analizi
# ----------------------------------
na_count = df.isna().sum().sort_values(ascending=False)
na_rate = (df.isna().mean() * 100).sort_values(ascending=False).round(3)
na_report = pd.DataFrame({"na_count": na_count, "na_rate_pct": na_rate})
print("\n>> Eksik Değer Raporu:")
print(na_report)
na_report.to_csv(os.path.join(OUTDIR, "missing_values.csv"))

# ----------------------------------
# 3) Adres Uzunluk İstatistikleri
# ----------------------------------
addr = df["address"].astype(str)
char_len = addr.str.len()
word_len = addr.str.split().map(len)

len_stats = pd.DataFrame({
    "char_len": char_len,
    "word_len": word_len
})
print("\n>> Uzunluk İstatistikleri (describe):")
print(len_stats.describe().T)
len_stats.describe().T.to_csv(os.path.join(OUTDIR, "length_stats.csv"))

# Dağılım bucket'ları
char_bins = pd.cut(char_len, bins=[0, 30, 60, 90, 120, 180, 9999], right=True)
word_bins = pd.cut(word_len, bins=[0, 4, 8, 12, 16, 25, 999], right=True)
char_dist = char_bins.value_counts().sort_index()
word_dist = word_bins.value_counts().sort_index()

print("\n>> Karakter uzunluk dağılımı:")
print(char_dist)
char_dist.to_csv(os.path.join(OUTDIR, "char_length_distribution.csv"))

print("\n>> Kelime uzunluk dağılımı:")
print(word_dist)
word_dist.to_csv(os.path.join(OUTDIR, "word_length_distribution.csv"))

# ----------------------------------
# 4) Label Analizi (varsa)
# ----------------------------------
if has_label:
    label_counts = df["label"].value_counts()
    print("\n>> Label sayısı (benzersiz):", label_counts.shape[0])
    print(">> En sık 10 label:")
    print(label_counts.head(10))
    label_counts.to_csv(os.path.join(OUTDIR, "label_counts.csv"))

    # Sınıf dengesizliği metrikleri
    gini = 1 - np.sum((label_counts/label_counts.sum())**2)
    print("\n>> Sınıf dengesizliği (Gini benzeri çeşitlilik endeksi):", round(gini, 6))

    # Head/Tail örnek
    head_labels = label_counts.head(10).index.tolist()
    tail_labels = label_counts.tail(10).index.tolist()
    df[df["label"].isin(head_labels)].head(20).to_csv(os.path.join(OUTDIR, "head_labels_sample.csv"), index=False)
    df[df["label"].isin(tail_labels)].head(20).to_csv(os.path.join(OUTDIR, "tail_labels_sample.csv"), index=False)

# ----------------------------------
# 5) Yinelenen Kayıt Analizi
# ----------------------------------
# Tam adres tekrarı
dup_addr_mask = df.duplicated(subset=["address"], keep=False)
dup_addr = df.loc[dup_addr_mask].sort_values("address")
print("\n>> Tam adres tekrarı adet:", dup_addr.shape[0])
dup_addr.head(50).to_csv(os.path.join(OUTDIR, "duplicate_full_address_samples.csv"), index=False)

# id bazlı olası tekrar (eğer id varsa, aynı id birden çok adres?)
if has_id:
    dup_id_mask = df.duplicated(subset=["id"], keep=False)
    dup_id = df.loc[dup_id_mask].sort_values("id")
    print(">> Aynı id tekrarları:", dup_id.shape[0])
    dup_id.head(50).to_csv(os.path.join(OUTDIR, "duplicate_id_samples.csv"), index=False)

# ----------------------------------
# 6) Türkçe Adres Token İstatistikleri
# ----------------------------------
# Basit anahtar kelimeler
KEY_TOKENS = ["mahalle", "mah", "mh", "cadde", "cad", "cd", "sokak", "sok", "sk",
              "bulvar", "blv", "no", "no.", "kat", "daire", "d:", "ap", "apt", "apartman",
              "sitesi", "blok", "bina", "mevkii", "caddesi", "sokağı", "sokagi"]
def contains_token(s, token):
    return int(re.search(rf"\b{re.escape(token)}\b", s) is not None)

addr_lower = addr.str.lower().fillna("")
token_presence = {f"has_{t}": addr_lower.map(lambda x: contains_token(x, t)) for t in KEY_TOKENS}
token_df = pd.DataFrame(token_presence)
token_summary = token_df.sum().sort_values(ascending=False)
print("\n>> Anahtar token varlık sayıları (ilk 20):")
print(token_summary.head(20))
token_summary.to_csv(os.path.join(OUTDIR, "token_presence_counts.csv"))

# ----------------------------------
# 7) Kısaltma & Varyasyon Frekansları
# ----------------------------------
VARIANTS = [
    ("mahalle", ["mah", "mh", "mhl"]),
    ("cadde",   ["cad", "cd"]),
    ("sokak",   ["sok", "sk"]),
    ("no",      ["no.", "nr", "numara"]),
]
rows = []
for canonical, vars_ in VARIANTS:
    row = {"canonical": canonical}
    row["canonical_count"] = addr_lower.str.contains(rf"\b{canonical}\b", regex=True).sum()
    for v in vars_:
        row[v] = addr_lower.str.contains(rf"\b{re.escape(v)}\b", regex=True).sum()
    rows.append(row)
variant_df = pd.DataFrame(rows)
print("\n>> Kısaltma/varyasyon sayıları:")
print(variant_df)
variant_df.to_csv(os.path.join(OUTDIR, "variant_counts.csv"), index=False)

# ----------------------------------
# 8) Noktalama, Rakam ve Özel Karakter İstatistikleri
# ----------------------------------
punct_counts = addr.str.count(r"[^\w\s]")
digit_counts = addr.str.count(r"\d")
non_tr_tr = addr.str.contains(r"[^\w\sçğıöşüÇĞİÖŞÜ.:/-]", regex=True)  # Türkçe dışı olası karakter
char_profile = pd.DataFrame({
    "punct_count": punct_counts,
    "digit_count": digit_counts,
    "has_non_tr_chars": non_tr_tr.astype(int)
})
print("\n>> Karakter profili (describe):")
print(char_profile.describe().T)
char_profile.describe().T.to_csv(os.path.join(OUTDIR, "char_profile_stats.csv"))

# ----------------------------------
# 9) n-gram Frekansları (1-gram, 2-gram, 3-gram)
# ----------------------------------
def tokenize_basic(s):
    return re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+", s.lower())

unigrams = Counter()
bigrams = Counter()
trigrams = Counter()

for s in addr_lower:
    toks = tokenize_basic(s)
    unigrams.update(toks)
    bigrams.update(zip(toks, toks[1:]))
    trigrams.update(zip(toks, toks[1:], toks[2:]))

def counter_to_df(counter, cols):
    items = counter.most_common()
    return pd.DataFrame(items, columns=cols)

uni_df = counter_to_df(unigrams, ["token", "count"])
bi_df  = counter_to_df(bigrams, ["token_pair", "count"])
tri_df = counter_to_df(trigrams, ["token_triplet", "count"])

print("\n>> En sık 30 unigram:")
print(uni_df.head(30))
print("\n>> En sık 30 bigram:")
print(bi_df.head(30))
print("\n>> En sık 30 trigram:")
print(tri_df.head(30))

uni_df.to_csv(os.path.join(OUTDIR, "unigram_counts.csv"), index=False)
bi_df.to_csv(os.path.join(OUTDIR, "bigram_counts.csv"), index=False)
tri_df.to_csv(os.path.join(OUTDIR, "trigram_counts.csv"), index=False)

# ----------------------------------
# 10) Olası Şüpheli Kayıtlar
# ----------------------------------
suspects = pd.DataFrame({
    "address": addr,
    "char_len": char_len,
    "word_len": word_len,
    "digit_count": digit_counts,
    "punct_count": punct_counts
})
rules = (
    (suspects["char_len"] < 10) |
    (suspects["word_len"] < 2) |
    (suspects["char_len"] > 180) |
    (suspects["digit_count"] == 0)  # çoğu adreste en az bir sayı beklenir (No, sokak no, daire vb.)
)
suspects_flagged = suspects[rules]
print("\n>> Şüpheli kayıt sayısı:", suspects_flagged.shape[0])
suspects_flagged.head(100).to_csv(os.path.join(OUTDIR, "suspect_records_sample.csv"), index=False)

print("\n[EDA TAMAMLANDI] Rapor CSV'leri 'eda_reports/' klasörüne kaydedildi.")
