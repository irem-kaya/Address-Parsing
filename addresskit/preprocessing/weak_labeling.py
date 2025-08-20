import pandas as pd
import yaml
import json
from addresskit.preprocessing.clean_text import normalize_text

# Doğru path'ler
HIER_PATH = "data/raw/turkiye_posta_hiyerarsi.json"
INDEX_PATH = "data/raw/turkiye_posta_index.json"

def load_config(path="configs/normalize.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# JSON'ları yükle
with open(HIER_PATH, "r", encoding="utf-8") as f:
    hier = json.load(f)

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    index = json.load(f)

def weak_label_address(addr: str, cfg: dict):
    text = normalize_text(addr, cfg)
    tokens = text.split()
    labels = ["O"] * len(tokens)

    for i, tok in enumerate(tokens):
        # Mahalle eşleşmesi
        if tok in index:
            labels[i] = "B-MAHALLE"
            continue
        # İl eşleşmesi
        for il in hier.keys():
            if tok == il:
                labels[i] = "B-IL"
                break
        # İlçe eşleşmesi
        for il, ilceler in hier.items():
            for ilce in ilceler.keys():
                if tok == ilce:
                    labels[i] = "B-ILCE"
                    break

    return {"tokens": tokens, "labels": labels}

if __name__ == "__main__":
    cfg = load_config()
    df = pd.read_csv("data/raw/train.csv")

    for i, row in df.head(5).iterrows():
        res = weak_label_address(row["address"], cfg)
        print("Original :", row["address"])
        print("Tokens   :", res["tokens"])
        print("Labels   :", res["labels"])
        print("="*60)
