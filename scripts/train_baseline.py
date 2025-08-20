# -*- coding: utf-8 -*-
"""
Adım 3: Özellik çıkarımı + Baz Model (TF-IDF + SGD-Logistic) + Tahmin
- Girdi: data/processed/train_clean_parsed.csv, test_clean_parsed.csv
- Çıktı: models/baseline/*.pkl, submissions/submission_baseline.csv
- Ölçek: ~848k satır, ~10k sınıf -> lineer ölçeklenebilir çözüm
"""

import os
import sys
import time
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
import joblib

# ----------------- I/O -----------------
PROC_DIR = os.path.join("data", "processed")
TRAIN_PATH = os.path.join(PROC_DIR, "train_clean_parsed.csv")
TEST_PATH  = os.path.join(PROC_DIR, "test_clean_parsed.csv")

MODELS_DIR = os.path.join("models", "baseline")
SUBMIT_DIR = "submissions"
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SUBMIT_DIR, exist_ok=True)

# ----------------- Yardımcı -----------------
def now():
    return time.strftime("%H:%M:%S")

def safe_col(df, c):
    return df[c].astype(str) if c in df.columns else pd.Series([""]*len(df))

def build_text_fields(df: pd.DataFrame):
    """
    Ana metin: address_clean
    Yan metin: ayrıştırılmış parçaların birleştirilmiş hali
    """
    base = safe_col(df, "address_clean")
    parts = []
    for c in ["mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce"]:
        parts.append(safe_col(df, c))
    side = (" ".join([c for c in ["mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce"]]))
    # üstteki sadece referans; asıl side_text aşağıda oluşturuluyor
    side_text = pd.Series([""]*len(df))
    for c in ["mahalle","cadde","sokak","no","daire","kat","bina_adi","mevkii","il","ilce"]:
        if c in df.columns:
            side_text = side_text.str.cat(df[c].astype(str), sep=" ")

    # final iki alan döndür
    return base.fillna(""), side_text.fillna("")

# ----------------- Vektörizerler -----------------
def make_vectorizers(max_features_char=500_000, max_features_word=150_000):
    """
    İki kanal: 
    - char TF-IDF (3-5), robust
    - word TF-IDF (1-2), tamamlayıcı
    Ayrı ayrı fitlenir ve FeatureUnion ile birleştirilir.
    """
    char_vect = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3,5),
        min_df=3,
        max_features=max_features_char,
        lowercase=False,  # zaten temiz
        norm="l2",
        sublinear_tf=True
    )
    word_vect = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1,2),
        min_df=3,
        max_features=max_features_word,
        lowercase=False,
        token_pattern=r"[a-z0-9çğıöşü]+",
        norm="l2",
        sublinear_tf=True
    )
    return char_vect, word_vect

def fit_transform_features(train_base, train_side, test_base, test_side):
    """
    İki ayrı vektörizeri hem base (address_clean) hem side (parça metni) için fitler;
    sonra birleştirir (yatay konkat).
    """
    print(f"[{now()}] TF-IDF vektörizer oluşturuluyor...")
    char_vect_base, word_vect_base = make_vectorizers()
    char_vect_side, word_vect_side = make_vectorizers(
        max_features_char=200_000, max_features_word=80_000
    )  # yan kanal daha küçük

    print(f"[{now()}] Fit (base/char)...")
    X_char_base_tr = char_vect_base.fit_transform(train_base)
    X_char_base_te = char_vect_base.transform(test_base)

    print(f"[{now()}] Fit (base/word)...")
    X_word_base_tr = word_vect_base.fit_transform(train_base)
    X_word_base_te = word_vect_base.transform(test_base)

    print(f"[{now()}] Fit (side/char)...")
    X_char_side_tr = char_vect_side.fit_transform(train_side)
    X_char_side_te = char_vect_side.transform(test_side)

    print(f"[{now()}] Fit (side/word)...")
    X_word_side_tr = word_vect_side.fit_transform(train_side)
    X_word_side_te = word_vect_side.transform(test_side)

    # birleştir
    from scipy.sparse import hstack
    X_tr = hstack([X_char_base_tr, X_word_base_tr, X_char_side_tr, X_word_side_tr]).tocsr()
    X_te = hstack([X_char_base_te, X_word_base_te, X_char_side_te, X_word_side_te]).tocsr()

    vect_bundle = {
        "char_vect_base": char_vect_base,
        "word_vect_base": word_vect_base,
        "char_vect_side": char_vect_side,
        "word_vect_side": word_vect_side
    }
    return X_tr, X_te, vect_bundle

# ----------------- Model -----------------
def make_model(n_classes: int):
    """
    SGDClassifier (log_loss) — büyük veri ve yüksek sınıf sayısı için pratik.
    class_weight='balanced' → nadir sınıflara biraz destek
    """
    clf = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=1e-5,              # gerektiğinde 1e-4..1e-6 arasında oynatılabilir
        max_iter=30,             # veri büyük; daha fazla iter gerekiyorsa artır
        tol=1e-3,
        early_stopping=True,
        n_iter_no_change=3,
        class_weight="balanced",
        random_state=42
    )
    return clf

# ----------------- Ana akış -----------------
def main():
    # 1) veriyi oku
    print(f"[{now()}] Loading train/test...")
    train = pd.read_csv(TRAIN_PATH)
    test  = pd.read_csv(TEST_PATH)

    assert "address_clean" in train.columns, "train_clean_parsed.csv içinde 'address_clean' bulunamadı."
    assert "label" in train.columns, "train verisinde 'label' kolonu yok."

    # 2) metinleri hazırla
    tr_base, tr_side = build_text_fields(train)
    te_base, te_side = build_text_fields(test)

    # 3) TF-IDF'leri fit et ve dönüştür
    X_tr, X_te, vect_bundle = fit_transform_features(tr_base, tr_side, te_base, te_side)

    # 4) etiket encode
    print(f"[{now()}] Label encode...")
    le = LabelEncoder()
    y = le.fit_transform(train["label"].values)

    # 5) CV ile hızlı değerlendirme (opsiyonel: süre için katmanlı 3-fold)
    print(f"[{now()}] CV eval (3-fold)...")
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    accs, f1s, top3s = [], [], []
    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_tr, y), 1):
        X_tr_f, X_va_f = X_tr[tr_idx], X_tr[va_idx]
        y_tr_f, y_va_f = y[tr_idx], y[va_idx]

        clf = make_model(n_classes=len(le.classes_))
        clf.fit(X_tr_f, y_tr_f)

        # val
        proba = clf.predict_proba(X_va_f)
        y_pred = proba.argmax(axis=1)

        acc = accuracy_score(y_va_f, y_pred)
        f1m = f1_score(y_va_f, y_pred, average="macro")
        # top-k (k=3), scikit >=1.0
        top3 = top_k_accuracy_score(y_va_f, proba, k=3, labels=np.arange(len(le.classes_)))

        accs.append(acc); f1s.append(f1m); top3s.append(top3)
        print(f"  Fold {fold}: acc={acc:.4f}  macroF1={f1m:.4f}  top3={top3:.4f}")

    print(f"[{now()}] CV mean: acc={np.mean(accs):.4f}  macroF1={np.mean(f1s):.4f}  top3={np.mean(top3s):.4f}")

    # 6) Tüm train ile yeniden eğit
    print(f"[{now()}] Fit full model...")
    clf_full = make_model(n_classes=len(le.classes_))
    clf_full.fit(X_tr, y)

    # 7) Test tahmini
    print(f"[{now()}] Predict test...")
    test_proba = clf_full.predict_proba(X_te)
    test_pred  = test_proba.argmax(axis=1)
    pred_labels = le.inverse_transform(test_pred)

    # 8) Submission oluştur
    sub = pd.DataFrame()
    if "id" in test.columns:
        sub["id"] = test["id"].values
    else:
        sub["id"] = np.arange(len(test))
    sub["label"] = pred_labels

    sub_path = os.path.join(SUBMIT_DIR, "submission_baseline.csv")
    sub.to_csv(sub_path, index=False)
    print(f"[{now()}] Wrote submission: {sub_path}  (rows={len(sub)})")

    # 9) Artefaktları kaydet (inference için)
    joblib.dump(vect_bundle, os.path.join(MODELS_DIR, "tfidf_bundle.pkl"))
    joblib.dump(le,           os.path.join(MODELS_DIR, "label_encoder.pkl"))
    joblib.dump(clf_full,     os.path.join(MODELS_DIR, "sgd_model.pkl"))
    print(f"[{now()}] Saved models to: {MODELS_DIR}")

    print(f"[{now()}] DONE.")

if __name__ == "__main__":
    main()
