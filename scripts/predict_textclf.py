# -*- coding: utf-8 -*-
"""
Eğitilmiş TF‑IDF + LR modelini yükler, test.csv için submission üretir.

Kullanım:
  python -m scripts.predict_textclf \
    --model models/tfidf_lr.joblib \
    --test_csv data/raw/test.csv \
    --out_csv submission.csv
"""

import os, sys, argparse, json, gzip, pickle, hashlib
import pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
PROC = os.path.join(DATA, "processed")
os.makedirs(PROC, exist_ok=True)

try:
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse
    from addresskit.preprocessing.postprocess import postprocess_parts
except Exception:
    sys.path.append(ROOT)
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse  # type: ignore
    from addresskit.preprocessing.postprocess import postprocess_parts  # type: ignore

def safe_str(x):
    if pd.isna(x): return ""
    s = str(x);  sl = s.lower()
    return "" if sl in {"nan","none"} else s

def make_signature(text: str) -> str:
    norm, parts = normalize_and_parse(safe_str(text))
    parts = postprocess_parts(norm, parts)
    keys = ("il","ilçe","mahalle","cadde","sokak","bina_adı","mevkii","no","kat","daire")
    sig  = " ".join(f"{k}:{parts[k]}" for k in keys if parts.get(k))
    return (norm + " | " + sig).strip()

def normalize_series(series: pd.Series) -> list:
    return [ make_signature(x) for x in series.fillna("").astype(str).tolist() ]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--test_csv", required=True)
    ap.add_argument("--out_csv", default=os.path.join(ROOT, "submission.csv"))
    args = ap.parse_args()

    import joblib
    bundle = joblib.load(args.model)
    vec, clf = bundle["vectorizer"], bundle["model"]

    df = pd.read_csv(args.test_csv)
    # id kolonu
    id_col = next((c for c in df.columns if str(c).lower() in {"id","index"}), None)
    ids = df[id_col].tolist() if id_col else list(range(1, len(df)+1))

    # adres kolonu
    text_col = next((c for c in df.columns if str(c).lower() in {"address","adres","full_address","text"}), None)
    if text_col is None:
        obj = df.select_dtypes(include=["object"]).columns
        text_col = obj[0] if len(obj) else df.columns[0]

    X = normalize_series(df[text_col])
    Xv = vec.transform(X)
    yhat = clf.predict(Xv)

    sub = pd.DataFrame({"id": ids, "label": yhat})
    sub.to_csv(args.out_csv, index=False)
    print(f"[OK] submission yazıldı -> {args.out_csv}")
    print(sub.head(5))

if __name__ == "__main__":
    main()
