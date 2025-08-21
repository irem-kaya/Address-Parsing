import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

# --- 1. Veri yolları ---
train_clean_path = "C:/Users/iremn/hackathon/address-hackathon/data/processed/train_clean_parsed.csv"
train_lowconf_path = "C:/Users/iremn/hackathon/address-hackathon/data/processed/train_low_confidence_cleaned.csv"

# --- 2. Verileri oku ---
df_clean = pd.read_csv(train_clean_path)
df_low = pd.read_csv(train_lowconf_path)

print("[DATA] clean:", df_clean.shape, ", low_conf:", df_low.shape)

# Label sütununu varsayıyorum -> "label"
y_clean = df_clean["label"].astype(str)
y_low = df_low["label"].astype(str)

# --- 3. Vektörleştirme ---
vectorizer = TfidfVectorizer(max_features=20000)
X_clean = vectorizer.fit_transform(df_clean["address"])
X_low = vectorizer.transform(df_low["address"])

# --- 4. Model (SGDClassifier) ---
clf = SGDClassifier(loss="log_loss", max_iter=5, random_state=42)

# --- 5. Train-Test Split ---
Xtr_c, Xte_c, ytr_c, yte_c = train_test_split(X_clean, y_clean, test_size=0.2, random_state=42)
Xtr_l, Xte_l, ytr_l, yte_l = train_test_split(X_low, y_low, test_size=0.2, random_state=42)

# --- 6. Eğitim (sadece clean üzerinde) ---
clf.fit(Xtr_c, ytr_c)

# --- 7. Raporlar ---
report_clean = classification_report(yte_c, clf.predict(Xte_c), output_dict=True)
report_low = classification_report(yte_l, clf.predict(Xte_l), output_dict=True)

# --- 8. DataFrame olarak kaydet ---
df_report_clean = pd.DataFrame(report_clean).transpose()
df_report_low = pd.DataFrame(report_low).transpose()

df_report_clean.to_csv("report_clean.csv")
df_report_low.to_csv("report_low.csv")

print("✅ Raporlar kaydedildi: report_clean.csv ve report_low.csv")
print("Clean dataset örnek sonuçları:\n", df_report_clean.head())
print("Low_conf dataset örnek sonuçları:\n", df_report_low.head())
