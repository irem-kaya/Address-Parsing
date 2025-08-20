# -*- coding: utf-8 -*-
"""
TF‑IDF + LogisticRegression ile adres sınıflandırma (label tahmini).
Validation F1 skorunu üretir, modeli kaydeder.

Kullanım (proje kökünden):
  python -m scripts.train_textclf \
    --train_csv data/raw/train.csv \
    --text_col address --label_col label \
    --min_df 2 --ngram_hi 2 --C 4.0 \
    --out models/tfidf_lr.joblib \
    --cv 0
"""

import os, sys, argparse, json, gzip, pickle, hashlib
import pandas as pd
from time import perf_counter

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
PROC = os.path.join(DATA, "processed")
os.makedirs(PROC, exist_ok=True)
os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)

# addresskit içe aktarımları
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

def train_val_split(df, label_col, val_size=0.15, seed=42):
    from sklearn.model_selection import train_test_split
    return train_test_split(df, df[label_col], test_size=val_size, random_state=seed, stratify=df[label_col])

def build_vectorizer(min_df=2, ngram_hi=2, max_features=None):
    from sklearn.feature_extraction.text import TfidfVectorizer
    return TfidfVectorizer(ngram_range=(1, ngram_hi), min_df=min_df, max_features=max_features)

def build_model(C=4.0):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(
        C=C, max_iter=2000, n_jobs=-1, solver="lbfgs", multi_class="auto"
    )

def cache_path(tag, path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1<<20):
            h.update(chunk)
    return os.path.join(PROC, f"{tag}_{h.hexdigest()}.pkl.gz")

def normalize_with_cache(series: pd.Series, tag: str, src_path: str):
    cp = cache_path(tag, src_path)
    if os.path.exists(cp):
        with gzip.open(cp, "rb") as f:
            print(f"[CACHE] Yükleniyor -> {os.path.basename(cp)}")
            return pickle.load(f)
    out = normalize_series(series)
    with gzip.open(cp, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[CACHE] Yazıldı  -> {os.path.basename(cp)}")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_csv", required=True)
    ap.add_argument("--text_col", default=None)
    ap.add_argument("--label_col", default="label")
    ap.add_argument("--val_size", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min_df", type=int, default=2)
    ap.add_argument("--ngram_hi", type=int, default=2)
    ap.add_argument("--max_features", type=int, default=None)
    ap.add_argument("--C", type=float, default=4.0)
    ap.add_argument("--out", default=os.path.join(ROOT, "models", "tfidf_lr.joblib"))
    ap.add_argument("--cv", type=int, default=0, help="KFold sayısı (0=holdout)")
    args = ap.parse_args()

    df = pd.read_csv(args.train_csv)
    if args.text_col is None:
        # otomatik adres kolonu bul
        for c in df.columns:
            if str(c).lower() in {"address","adres","full_address","text"}:
                args.text_col = c; break
        if args.text_col is None:
            # ilk object kolonu al
            obj = df.select_dtypes(include=["object"]).columns
            args.text_col = obj[0] if len(obj) else df.columns[0]

    print(f"[INFO] text_col={args.text_col}, label_col={args.label_col}")

    # normalize + imza (cache)
    X_all = normalize_with_cache(df[args.text_col], "train_norm", args.train_csv)
    y_all = df[args.label_col].tolist()

    if args.cv and args.cv > 1:
        # KFold F1
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import f1_score
        from numpy import mean
        skf = StratifiedKFold(n_splits=args.cv, shuffle=True, random_state=args.seed)
        scores = []
        for fold, (tr, va) in enumerate(skf.split(X_all, y_all), 1):
            vec = build_vectorizer(args.min_df, args.ngram_hi, args.max_features)
            Xtr = vec.fit_transform([X_all[i] for i in tr])
            Xva = vec.transform([X_all[i] for i in va])
            clf = build_model(args.C).fit(Xtr, [y_all[i] for i in tr])
            pred = clf.predict(Xva)
            f1 = f1_score([y_all[i] for i in va], pred, average="macro")
            print(f"[CV] fold {fold}: F1_macro={f1:.4f}")
            scores.append(f1)
        print(f"[CV] mean F1_macro={mean(scores):.4f}")
        # Tam veride eğitip kaydet
        vec = build_vectorizer(args.min_df, args.ngram_hi, args.max_features)
        X = vec.fit_transform(X_all)
        clf = build_model(args.C).fit(X, y_all)
    else:
        # Hold‑out F1
        from sklearn.metrics import f1_score, classification_report
        train_df, val_df, y_tr, y_va = train_val_split(df, args.label_col, args.val_size, args.seed)
        Xtr = normalize_with_cache(train_df[args.text_col], "train_norm_holdout", args.train_csv)
        Xva = normalize_series(val_df[args.text_col])

        vec = build_vectorizer(args.min_df, args.ngram_hi, args.max_features)
        Xtr_m = vec.fit_transform(Xtr)
        Xva_m = vec.transform(Xva)

        clf = build_model(args.C).fit(Xtr_m, y_tr.tolist())
        pred = clf.predict(Xva_m)
        f1_macro = __import__("sklearn.metrics").metrics.f1_score(y_va.tolist(), pred, average="macro")
        f1_micro = __import__("sklearn.metrics").metrics.f1_score(y_va.tolist(), pred, average="micro")
        print(f"[VAL] F1_macro={f1_macro:.4f} | F1_micro={f1_micro:.4f}")
        print("[VAL] classification report (kısa):")
        print(__import__("sklearn.metrics").metrics.classification_report(y_va.tolist(), pred)[:800])

        # Tüm veride tekrar eğit → kaydet
        vec = build_vectorizer(args.min_df, args.ngram_hi, args.max_features)
        X_all_m = vec.fit_transform(X_all)
        clf = build_model(args.C).fit(X_all_m, y_all)

    # modeli kaydet
    import joblib
    joblib.dump({"vectorizer": vec, "model": clf}, args.out)
    print(f"[OK] model kaydedildi -> {args.out}")

if __name__ == "__main__":
    main()
