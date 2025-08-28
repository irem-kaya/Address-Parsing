# ============================================================
# HIZLI ÇALIŞAN TAM BORU HATTI
# TF-IDF -> SVD(256) -> L2 Normalize -> SGDClassifier (early_stopping)
# ============================================================

import gc
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import Normalizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, fbeta_score
)

# ---------- 0) Parametreler ----------
TRAIN_CLEAN_PATH = r"C:/Users/iremn/hackathon/address-hackathon/data/processed/train_clean_parsed.csv"
TRAIN_LOWCONF_PATH = r"C:/Users/iremn/hackathon/address-hackathon/data/processed/train_low_confidence_cleaned.csv"

MAX_FEATURES = 200_000     # hız için 200k (gerekirse 150k/250k deneyebilirsin)
NGRAM = (1, 2)
MIN_DF = 3                 # çok nadir n-gramları at
SVD_COMPONENTS = 256       # 128-384 arası hız/doğruluk dengesi
SVD_SAMPLE = 200_000       # SVD fit için örnek boyutu (hız için)
RANDOM_STATE = 42
TEST_SIZE = 0.20

# ---------- 1) Veriyi oku ----------
df_clean = pd.read_csv(TRAIN_CLEAN_PATH)
df_lowconf = pd.read_csv(TRAIN_LOWCONF_PATH)

print("[DATA] clean:", df_clean.shape, ", low_conf:", df_lowconf.shape)

# Sadece gerekli kolonlar
df_clean = df_clean[["address", "label"]].dropna()

# İstersen düşük güven verisini de ekleyebilirsin (yorum aç):
# df_low = df_lowconf[["address","label"]].dropna()
# df_all = pd.concat([df_clean, df_low], ignore_index=True)
df_all = df_clean

# ---------- 2) Train/Test split ----------
X_train, X_test, y_train, y_test = train_test_split(
    df_all["address"], df_all["label"],
    test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df_all["label"]
)

# ---------- 3) TF-IDF (sparse, sonra float32) ----------
vectorizer = TfidfVectorizer(
    max_features=MAX_FEATURES,
    ngram_range=NGRAM,
    min_df=MIN_DF
)

X_train_vec = vectorizer.fit_transform(X_train).astype(np.float32)
X_test_vec  = vectorizer.transform(X_test).astype(np.float32)

print("X_train_vec:", X_train_vec.shape, X_train_vec.dtype)
print("X_test_vec :", X_test_vec.shape,  X_test_vec.dtype)

# ---------- 4) Hızlı SVD (randomized) ----------
svd = TruncatedSVD(
    n_components=SVD_COMPONENTS,
    algorithm="randomized",
    n_iter=2,
    random_state=RANDOM_STATE
)

# SVD'yi tüm veride değil, örneklemde fit et (çok hızlanır)
rng = np.random.default_rng(RANDOM_STATE)
sample_size = min(SVD_SAMPLE, X_train_vec.shape[0])
sample_idx = rng.choice(X_train_vec.shape[0], size=sample_size, replace=False)
svd.fit(X_train_vec[sample_idx])

# Tüm veriyi indirgenmiş uzaya projekte et (yoğun matris döner)
X_train_red = svd.transform(X_train_vec).astype(np.float32)
X_test_red  = svd.transform(X_test_vec).astype(np.float32)

# Artık büyük sparse TF-IDF'lere ihtiyacın yok → bellek boşalt
del X_train_vec, X_test_vec
gc.collect()

# ---------- 5) L2 normalize (cosine-benzeri) ----------
norm = Normalizer(copy=False)
X_train_red = norm.fit_transform(X_train_red)
X_test_red  = norm.transform(X_test_red)

print("Reduced shapes:", X_train_red.shape, X_test_red.shape)

# ---------- 6) Hızlı sınıflandırıcı (early stopping) ----------
clf = SGDClassifier(
    loss="log_loss",          # "modified_huber" da denenebilir (hızlı/sağlam)
    alpha=1e-5,
    random_state=RANDOM_STATE,
    average=True,
    early_stopping=True,
    n_iter_no_change=3,
    validation_fraction=0.1
)
clf.fit(X_train_red, y_train)

# ---------- 7) Tahmin ----------
y_pred = clf.predict(X_test_red)

# ---------- 8) Skorlar (KeyError yok, doğrudan hesap) ----------
acc         = round(accuracy_score(y_test, y_pred), 4)
macro_f1    = round(f1_score(y_test, y_pred, average="macro",    zero_division=0), 4)
micro_f1    = round(f1_score(y_test, y_pred, average="micro",    zero_division=0), 4)   # tek etiketli multiclass'ta ≡ accuracy
weighted_f1 = round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4)

macro_f2    = round(fbeta_score(y_test, y_pred, beta=2, average="macro",    zero_division=0), 4)
micro_f2    = round(fbeta_score(y_test, y_pred, beta=2, average="micro",    zero_division=0), 4)
weighted_f2 = round(fbeta_score(y_test, y_pred, beta=2, average="weighted", zero_division=0), 4)

print("\n[SUMMARY]")
print("Accuracy   :", acc)
print("Macro F1   :", macro_f1)
print("Micro F1   :", micro_f1)
print("Weighted F1:", weighted_f1)
print("Macro F2   :", macro_f2)
print("Micro F2   :", micro_f2)
print("Weighted F2:", weighted_f2)
