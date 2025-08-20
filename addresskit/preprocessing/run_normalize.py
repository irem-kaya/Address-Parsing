# -*- coding: utf-8 -*-
import os, json
import pandas as pd

# paket içi importlar
from .normalize_and_parse import normalize_and_parse
from addresskit.preprocessing.postprocess import postprocess_parts


HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(ROOT, "data", "processed")
os.makedirs(DATA_PROCESSED, exist_ok=True)

def find_address_col(df: pd.DataFrame) -> str:
    candidates = {"address","adres","full_address","text"}
    for c in df.columns:
        if str(c).lower() in candidates:
            return c
    obj_cols = df.select_dtypes(include=["object"]).columns
    if len(obj_cols) == 0:
        raise ValueError("Adres metni için object tipinde bir kolon bulunamadı.")
    return obj_cols[0]

def main():
    train_p = os.path.join(DATA_RAW, "train.csv")
    if not os.path.exists(train_p):
        raise FileNotFoundError(f"Bulunamadı: {train_p}")
    df = pd.read_csv(train_p)

    text_col = find_address_col(df)
    # NaN/None temizliği
    df[text_col] = (
        df[text_col]
        .where(df[text_col].notna(), "")
        .astype(str)
        .replace({"None":"", "nan":"", "NaN":""})
    )

    norms, parts_list = [], []
    for i, addr in enumerate(df[text_col]):
        norm, parts = normalize_and_parse(addr)
        parts = postprocess_parts(norm, parts)
        norms.append(norm)
        parts_list.append(parts)

        if i < 5:
            print("\n" + "="*60)
            print("Original :", addr)
            print("Normalized:", norm)
            print("Parts    :", parts)

    df_out = df.copy()
    df_out["normalized"] = norms
    df_out["parts"] = [json.dumps(p, ensure_ascii=False) for p in parts_list]

    out_csv  = os.path.join(DATA_PROCESSED, "train_labeled.csv")
    out_json = os.path.join(DATA_PROCESSED, "train_labeled.json")
    df_out.to_csv(out_csv, index=False, encoding="utf-8")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(df_out.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    print(f"\nKaydedildi:\n- {out_csv}\n- {out_json}")

if __name__ == "__main__":
    main()
