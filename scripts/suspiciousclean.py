import pandas as pd
import re
import os

# --- 1) Dosya yolları (gerekirse düzenle) ---
train_path = r"C:/Users/iremn/hackathon/address-hackathon/data/processed/train_clean_parsed.csv"
susp_path  = r"C:/Users/iremn/hackathon/address-hackathon/data/processed/train_clean_parsed_suspicious.csv"

# Çıktılar (birleştirme YOK)
baseline_out     = r"train_clean_final_baseline.csv"          # opsiyonel
lowconf_only_out = r"train_low_confidence_cleaned.csv"
report_out       = r"train_lowconf_cleaning_report.csv"

# --- 2) Oku ---
train = pd.read_csv(train_path, encoding="utf-8", engine="python")
susp  = pd.read_csv(susp_path,  encoding="utf-8", engine="python")

# --- 3) Baseline işaretle (kaydetmek istersen en alttaki satırı aç) ---
train["confidence_flag"] = "clean"
train["sample_weight"] = 1.0

# --- 4) Suspicious temizlik ---
ONLY_PUNCT_SP_RE = re.compile(r"^[\s\W_]+$")

def is_bad_address(series):
    s = series.astype(str)
    cond_empty = s.str.strip() == ""
    cond_short = s.str.len() < 6
    cond_only_punct = s.str.match(ONLY_PUNCT_SP_RE).fillna(False)
    return cond_empty | cond_short | cond_only_punct

s0 = susp.copy()

# Adres sütunlarını garanti altına al
if "address" not in s0.columns and "address_clean" in s0.columns:
    s0["address"] = s0["address_clean"]
if "address_clean" not in s0.columns and "address" in s0.columns:
    s0["address_clean"] = s0["address"]

initial_rows = len(s0)

# a) Boş/çok kısa/sadece noktalama adresleri at
bad_rows_mask = is_bad_address(s0["address"]) | is_bad_address(s0["address_clean"])
s1 = s0.loc[~bad_rows_mask].copy()
dropped_bad = int(bad_rows_mask.sum())

# b) Tam satır duplicate’leri at
before = len(s1)
s1 = s1.drop_duplicates()
dropped_exact_dups = before - len(s1)

# c) address_clean bazlı duplicate’leri at
before2 = len(s1)
s1 = s1.drop_duplicates(subset=["address_clean"])
dropped_clean_dups = before2 - len(s1)

# d) low confidence etiketi ve opsiyonel ağırlık
s1["confidence_flag"] = "low_confidence"
s1["sample_weight"] = 0.5

# --- 5) Raporla & Kaydet (birleştirme yok) ---
report = {
    "suspicious_rows_in": [initial_rows],
    "dropped_bad_address": [dropped_bad],
    "dropped_exact_dups": [dropped_exact_dups],
    "dropped_clean_dups": [dropped_clean_dups],
    "lowconf_rows_out": [len(s1)],
    "baseline_rows": [len(train)]
}
report_df = pd.DataFrame(report)

s1.to_csv(lowconf_only_out, index=False, encoding="utf-8-sig")
report_df.to_csv(report_out, index=False, encoding="utf-8-sig")

# Baseline’ı dosyaya yazmak istersen yorum satırını aç
# train.to_csv(baseline_out, index=False, encoding="utf-8-sig")

print("✅ Kaydedildi:")
print(f" - {lowconf_only_out} (temizlenmiş suspicious)")
print(f" - {report_out} (özet rapor)")
# print(f" - {baseline_out} (opsiyonel: clean train)")
