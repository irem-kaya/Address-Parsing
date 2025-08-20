# -*- coding: utf-8 -*-
"""
TF‑IDF en yakın komşu baseline (paralel + cache'li).
Kullanım (proje kökünden):
  python -m scripts.baseline_submission \
    --min_df 2 --ngram_hi 2 --n_jobs -1 --max_features 300000
"""

import os, sys, json, gzip, pickle, hashlib, argparse
from time import perf_counter
from joblib import Parallel, delayed

import pandas as pd

# ---------- Yollar ----------
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
PROC = os.path.join(DATA, "processed")
os.makedirs(PROC, exist_ok=True)

# ---------- Paket importları ----------
try:
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse
    from addresskit.preprocessing.postprocess import postprocess_parts
except Exception:
    sys.path.append(ROOT)
    from addresskit.preprocessing.normalize_and_parse import normalize_and_parse  # type: ignore
    from addresskit.preprocessing.postprocess import postprocess_parts  # type: ignore

# ---------- Yardımcılar ----------
def pick_text_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        if str(c).lower() in {"address", "adres", "full_address", "text"}:
            return c
    obj = df.select_dtypes(include=["object"]).columns
    return obj[0] if len(obj) else df.columns[0]

def pick_label_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        if str(c).lower() in {"label", "labels", "target"}:
            return c
    return df.columns[-1]

def safe_str(x) -> str:
    if pd.isna(x): return ""
    s = str(x)
    return "" if s.lower() in {"nan","none"} else s

def _hash_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1<<20):
            h.update(chunk)
    return h.hexdigest()

def _cache_path(tag: str, src_path: str) -> str:
    return os.path.join(PROC, f"{tag}_{_hash_file(src_path)}.pkl.gz")

def _normalize_one(s: str) -> str:
    norm, parts = normalize_and_parse(safe_str(s))
    parts = postprocess_parts(norm, parts)
    sig_keys = ("mahalle","cadde","sokak","no","kat","daire","ilçe","il","bina_adı","mevkii")
    sig = " ".join(f"{k}:{parts[k]}" for k in sig_keys if parts.get(k))
    return (norm + " | " + sig).strip()

def normalize_series_with_cache(series: pd.Series, tag: str, src_path: str, n_jobs=-1, chunk=2000):
    cpath = _cache_path(tag, src_path)
    if os.path.exists(cpath):
        with gzip.open(cpath, "rb") as f:
            print(f"[CACHE] Yükleniyor -> {os.path.basename(cpath)}")
            return pickle.load(f)

    texts = series.fillna("").astype(str).tolist()
    print(f"[INFO] Normalize başlıyor (n={len(texts)}, jobs={n_jobs})")
    t0 = perf_counter()

    def norm_chunk(lst):  # tek işlemci bir parça
        return [_normalize_one(x) for x in lst]

    parts = Parallel(n_jobs=n_jobs, prefer="threads", verbose=5)(
        delayed(norm_chunk)(texts[i:i+chunk])
        for i in range(0, len(texts), chunk)
    )
    res = [y for ch in parts for y in ch]
    print(f"[OK] Normalize bitti. Süre: {perf_counter()-t0:.1f}s")

    with gzip.open(cpath, "wb") as f:
        pickle.dump(res, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[CACHE] Yazıldı -> {os.path.basename(cpath)}")
    return res

def build_tfidf_index(train_texts, min_df=2, max_features=None, ngram_hi=2):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.neighbors import NearestNeighbors
    vec = TfidfVectorizer(ngram_range=(1, ngram_hi),
                          min_df=min_df,
                          max_features=max_features)
    X = vec.fit_transform(train_texts)
    nn = NearestNeighbors(n_neighbors=1, metric="cosine").fit(X)
    return vec, nn, X.shape

def tfidf_nn_predict(vec, nn, query_texts, train_labels):
    Xq = vec.transform(query_texts)
    dists, idxs = nn.kneighbors(Xq, n_neighbors=1)
    labels = [train_labels[i[0]] for i in idxs]
    sims = [(1.0 - float(d[0])) for d in dists]
    return labels, sims

# ---------- Ana akış ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_csv", default=os.path.join(RAW, "train.csv"))
    ap.add_argument("--test_csv",  default=os.path.join(RAW, "test.csv"))
    ap.add_argument("--out_csv",   default=os.path.join(ROOT, "submission.csv"))
    ap.add_argument("--min_df", type=int, default=2)
    ap.add_argument("--ngram_hi", type=int, default=2)
    ap.add_argument("--max_features", type=int, default=None)
    ap.add_argument("--limit_train", type=int, default=None)
    ap.add_argument("--limit_test", type=int, default=None)
    ap.add_argument("--n_jobs", type=int, default=-1)  # -1 = tüm çekirdekler
    args = ap.parse_args()

    if not os.path.exists(args.train_csv): raise FileNotFoundError(args.train_csv)
    if not os.path.exists(args.test_csv):  raise FileNotFoundError(args.test_csv)

    train = pd.read_csv(args.train_csv)
    test  = pd.read_csv(args.test_csv)

    if args.limit_train: train = train.head(args.limit_train)
    if args.limit_test:  test  = test.head(args.limit_test)

    print("[CHK] train rows:", len(train), "cols:", list(train.columns)[:6], "...")
    print("[CHK] test  rows:", len(test),  "cols:", list(test.columns)[:6],  "...")

    text_col   = pick_text_col(train)
    label_col  = pick_label_col(train)
    test_text  = pick_text_col(test)

    # id
    id_col = next((c for c in test.columns if str(c).lower() in {"id","index"}), None)
    ids = test[id_col].tolist() if id_col else list(range(1, len(test)+1))

    # ---- normalize (paralel + cache)
    print("[INFO] Train normalize ediliyor...")
    tr_norm = normalize_series_with_cache(train[text_col], "train_norm",
                                          src_path=args.train_csv, n_jobs=args.n_jobs)
    print("[INFO] Test normalize ediliyor...")
    te_norm = normalize_series_with_cache(test[test_text], "test_norm",
                                          src_path=args.test_csv, n_jobs=args.n_jobs)

    # ---- TF‑IDF + 1‑NN
    from sklearn.exceptions import ConvergenceWarning  # sadece import, uyarı yok
    vec, nn, shape = build_tfidf_index(tr_norm,
                                       min_df=args.min_df,
                                       max_features=args.max_features,
                                       ngram_hi=args.ngram_hi)
    print(f"[INFO] TF‑IDF matrisi: {shape[0]} x {shape[1]}")
    t0 = perf_counter()
    preds, sims = tfidf_nn_predict(vec, nn, te_norm, train[label_col].tolist())
    print(f"[OK] En yakın komşu sorgu bitti. Süre: {perf_counter()-t0:.1f}s")

    # ---- submission
    sub = pd.DataFrame({"id": ids, "label": preds})
    sub.to_csv(args.out_csv, index=False)
    print(f"[OK] Submission yazıldı -> {args.out_csv}")
    if sims:
        print("[INFO] Ortalama benzerlik:", round(float(pd.Series(sims).mean()), 3))

    # küçük örnek log
    for i in range(min(3, len(te_norm))):
        print("\n" + "="*60)
        print("Query  :", te_norm[i][:120] + ("..." if len(te_norm[i])>120 else ""))
        print("Label  :", preds[i])
        print("Sim    :", round(sims[i], 3))

if __name__ == "__main__":
    main()
