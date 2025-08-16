import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

def fit_knn(train_texts, ngram_range=(3, 6), max_features=1500000):
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=ngram_range, max_features=max_features)
    X_train = vectorizer.fit_transform(train_texts)
    knn = NearestNeighbors(metric="cosine", algorithm="brute")
    knn.fit(X_train)
    return vectorizer, knn, X_train

def predict_knn(test_texts, vectorizer, knn, X_train, train_labels, top_k=1):
    X_test = vectorizer.transform(test_texts)
    distances, indices = knn.kneighbors(X_test, n_neighbors=top_k)
    preds = []
    confs = []
    for dist, idx in zip(distances, indices):
        preds.append(train_labels.iloc[idx[0]])
        confs.append(1 - dist[0])  # cosine similarity
    return preds, confs

def run_match(train_path, test_path, out_path):
    # Verileri oku
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Fit KNN
    vectorizer, knn, X_train = fit_knn(train_df["address_norm"])

    # Predict
    preds, confs = predict_knn(test_df["address_norm"], vectorizer, knn, X_train, train_df["label"])

    # Sonuçları kaydet
    out_df = pd.DataFrame({
        "id": test_df["id"],
        "label_pred": preds,
        "confidence": confs
    })
    out_df.to_parquet(out_path, index=False)
    print(f"Saved predictions to {out_path}")
