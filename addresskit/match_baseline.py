# addresskit/match_baseline.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import argparse

print("match_baseline started...")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, help="Normalized train CSV")
    parser.add_argument("--test", required=True, help="Normalized test CSV")
    parser.add_argument("--out", required=True, help="Output CSV for submission")
    args = parser.parse_args()

    # 1. Verileri oku
    print("📂 Reading data...")
    train_df = pd.read_csv(args.train)
    test_df = pd.read_csv(args.test)

    # 2. TF-IDF vektörleştirme
    print("🔤 Vectorizing text...")
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    X_train = vectorizer.fit_transform(train_df["address"].astype(str))
    X_test = vectorizer.transform(test_df["address"].astype(str))

    # 3. KNN ile en yakın komşu bulma
    print("🔍 Finding nearest neighbors...")
    knn = NearestNeighbors(n_neighbors=1, metric="cosine")
    knn.fit(X_train)
    distances, indices = knn.kneighbors(X_test)

    # 4. Tahminleri oluştur
    print("📝 Creating predictions...")
    preds = train_df.iloc[indices.flatten()]["address_id"].values
    submission = pd.DataFrame({
        "id": test_df["id"],
        "match_id": preds
    })

    # 5. Kaydet
    submission.to_csv(args.out, index=False)
    print(f"✅ Submission file saved to {args.out}")

if __name__ == "__main__":
    main()
