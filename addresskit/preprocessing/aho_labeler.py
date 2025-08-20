# addresskit/preprocessing/aho_labeler.py

import pandas as pd
import json
import ahocorasick
import os

# --- 1. JSON sözlükleri yükle ---
HIER_JSON = "data/raw/turkiye_posta_hiyerarsi.json"
INDEX_JSON = "data/raw/turkiye_posta_index.json" 
TRAIN_PATH = "data/raw/train.csv"   # senin adres verin
OUT_PATH = "data/processed/train_labeled.csv"

with open(INDEX_JSON, "r", encoding="utf-8") as f:
    index_dict = json.load(f)

# --- 2. Aho Automaton hazırla ---
automaton = ahocorasick.Automaton()
for word in index_dict.keys():
    automaton.add_word(word.lower(), word.lower())
automaton.make_automaton()

def label_address(address: str):
    tokens = address.lower().split()
    labels = ["O"] * len(tokens)

    for i, tok in enumerate(tokens):
        for end_idx, found in automaton.iter(tok):
            if found in index_dict:
                info = index_dict[found]
                if "il" in info:
                    labels[i] = "B-ILCE"
                if "il" in info and i+1 < len(tokens):
                    labels[i] = "B-IL"
    return tokens, labels

# --- 3. Adresleri işle ---
df = pd.read_csv(TRAIN_PATH)
results = []

for i, row in df.head(100).iterrows():  # sadece ilk 100 adres test için
    tokens, labels = label_address(row["address"])
    for t, l in zip(tokens, labels):
        results.append({"id": i, "address": row["address"], "token": t, "label": l})

out_df = pd.DataFrame(results)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
out_df.to_csv(OUT_PATH, index=False, encoding="utf-8")

print(f"✅ İlk 100 adres etiketlendi → {OUT_PATH}")
