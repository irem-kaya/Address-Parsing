# scripts/make_match_preview.py
import argparse
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--left", required=True)
ap.add_argument("--right", required=True)
ap.add_argument("--match", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

L = pd.read_csv(args.left)
R = pd.read_csv(args.right)
M = pd.read_csv(args.match)

# match.csv'deki id'leri string'e çevir (dtype tutarsızlığı önlemek için)
for col in ("left_id", "right_id"):
    if col in M.columns:
        M[col] = M[col].astype(str)

# left/right'ta id kolonu yoksa index'ten üret
if "id" in L.columns:
    L = L.rename(columns={"id": "left_id"})
else:
    L = L.reset_index().rename(columns={"index": "left_id"})
if "id" in R.columns:
    R = R.rename(columns={"id": "right_id"})
else:
    R = R.reset_index().rename(columns={"index": "right_id"})

L["left_id"] = L["left_id"].astype(str)
R["right_id"] = R["right_id"].astype(str)

# merge: solda left, sağda right; sağ kolonlara _R suffix
df = M.merge(L, on="left_id", how="left", suffixes=("", "_L")).merge(
    R, on="right_id", how="left", suffixes=("", "_R")
)

# metinleri güvenli şekilde seç
left_text = df["address_norm"].where(df["address_norm"].notna(), df.get("address", ""))
right_text = df.get("address_norm_R", df.get("address_R", ""))

out = pd.DataFrame(
    {
        "left_id": df["left_id"],
        "left_text": left_text,
        "right_id": df["right_id"],
        "right_text": right_text,
        "score": df["score"],
    }
)

out.to_csv(args.out, index=False, encoding="utf-8")
print(f"[preview] wrote -> {args.out}; rows={len(out)}")
