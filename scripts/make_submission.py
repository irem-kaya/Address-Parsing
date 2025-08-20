# -*- coding: utf-8 -*-
"""
test.csv -> submission.csv üretir.
Kullanım (proje kökünden):
    python -m scripts.make_submission
Opsiyonlar:
    python -m scripts.make_submission --prediction_mode parts_string|parts_json|normalized
    python -m scripts.make_submission --test_csv data/raw/test.csv --out_csv submission.csv
"""

import os
import sys
import json
import argparse
import pandas as pd

# ---- Yol/klasörler
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA_DIR = os.path.join(ROOT, "data")
DATA_RAW = os.path.join(DATA_DIR, "raw")

# ---- Paket importları (önce normal, olmazsa path'e kökü ekle)
try:
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse
    from addresskit.preprocessing.postprocess import postprocess_parts
except Exception:
    sys.path.append(ROOT)  # kökü PYTHONPATH'e ekle
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse  # type: ignore
    from addresskit.preprocessing.postprocess import postprocess_parts  # type: ignore


# ---- Yardımcılar
def pick_text_column(df: pd.DataFrame) -> str:
    """Adres metni kolonunu otomatik seç."""
    candidates = {"address", "adres", "full_address", "text"}
    for c in df.columns:
        if str(c).lower() in candidates:
            return c
    obj_cols = df.select_dtypes(include=["object"]).columns
    return obj_cols[0] if len(obj_cols) else df.columns[0]


def safe_str(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x)
    # 'nan' ve 'None' stringlerini temizle
    return "" if s.lower() in {"nan", "none"} else s


def stringify_parts(parts: dict) -> str:
    """Tek kolonluk okunabilir çıktı."""
    order = ["il", "ilçe", "mahalle", "cadde", "sokak",
             "bina_adı", "mevkii", "no", "kat", "daire"]
    chunks = []
    for k in order:
        if k in parts and parts[k]:
            chunks.append(f"{k}:{parts[k]}")
    return " | ".join(chunks)


def load_sample_template():
    """sample_submission.csv varsa kolon düzenini döndür (id_col, pred_col, columns)."""
    sample_p = os.path.join(DATA_DIR, "sample_submission.csv")
    if os.path.exists(sample_p):
        try:
            ss = pd.read_csv(sample_p, nrows=5)
            cols = list(ss.columns)
            if len(cols) >= 2:
                id_col, pred_col = cols[0], cols[-1]
                print(f"[INFO] sample_submission bulundu. Kolonlar: {cols}")
                return id_col, pred_col, cols
        except Exception as e:
            print(f"[WARN] sample_submission okunamadı: {e}")
    # varsayılan
    return "id", "prediction", None


# ---- Ana akış
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test_csv", default=os.path.join(DATA_RAW, "test.csv"))
    ap.add_argument("--out_csv", default=os.path.join(ROOT, "submission.csv"))
    ap.add_argument("--prediction_mode",
                    choices=["parts_string", "parts_json", "normalized"],
                    default="parts_string",
                    help="Tek kolonlu submission için çıktı modu.")
    args = ap.parse_args()

    # test.csv oku
    if not os.path.exists(args.test_csv):
        raise FileNotFoundError(f"Bulunamadı: {args.test_csv}")
    df = pd.read_csv(args.test_csv)
    if len(df) == 0:
        raise ValueError("test.csv boş görünüyor.")

    # id/pred kolon adları
    id_col, pred_col, template_cols = load_sample_template()

    # adres sütunu
    text_col = pick_text_column(df)
    print(f"[INFO] Adres kolonu: {text_col}")

    # id yoksa sıradan üret
    ids = df[id_col].tolist() if id_col in df.columns else list(range(1, len(df) + 1))

    preds = []
    for i, txt in enumerate(df[text_col].tolist()):
        norm, parts = normalize_and_parse(safe_str(txt))
        parts = postprocess_parts(norm, parts)  # <<< DİKKAT: imza (norm, parts)

        # tek kolonluk prediction değeri
        if args.prediction_mode == "normalized":
            pred_value = norm
        elif args.prediction_mode == "parts_json":
            pred_value = json.dumps({k: v for k, v in parts.items() if not k.startswith("_")},
                                    ensure_ascii=False)
        else:
            pred_value = stringify_parts({k: v for k, v in parts.items() if not k.startswith("_")})

        preds.append(pred_value)

        if i < 5:
            print("\n" + "=" * 60)
            print("Original :", txt)
            print("Normalized:", norm)
            print("Parts    :", parts)

    # submission'ı kur
    if template_cols is not None:
        sub = pd.DataFrame({id_col: ids})
        sub[pred_col] = preds
        # şablonda başka kolonlar varsa boş geç
        for c in template_cols:
            if c not in sub.columns:
                sub[c] = ""
        sub = sub[template_cols]
    else:
        sub = pd.DataFrame({id_col: ids, pred_col: preds})

    sub.to_csv(args.out_csv, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Submission yazıldı -> {args.out_csv}")
    print(sub.head(3))


if __name__ == "__main__":
    # kökten çalıştır: python -m scripts.make_submission
    # yine de doğrudan çağırımda çalışsın diye kökü path'e ekledik (yukarıda).
    main()
