import argparse
import yaml
import pandas as pd
from ..utils.io import ensure_parent_dir
from .clean_text import load_config, normalize_text, extract_parts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    # Config yükle
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = load_config(yaml.safe_load(f))

    # Adres kolonunu string olarak oku
    df = pd.read_csv(args.input, dtype={"address": str})

    prim, sec, mh, sk, cd, no, dr, kt = [], [], [], [], [], [], [], []

    for addr in df["address"].tolist():
        addr_str = "" if pd.isna(addr) else str(addr)
        p, s = normalize_text(addr_str, cfg)

        # 🔹 Parçaları çıkar
        parts = extract_parts(p, cfg)

        prim.append(p)
        sec.append(s)
        mh.append(parts.get("mahalle"))
        sk.append(parts.get("sokak"))
        cd.append(parts.get("cadde"))
        no.append(parts.get("no"))
        dr.append(parts.get("daire"))
        kt.append(parts.get("kat"))

    df["address_norm"] = prim
    df["address_norm_ascii"] = sec
    df["mahalle"] = mh
    df["sokak"] = sk
    df["cadde"] = cd
    df["no"] = no
    df["daire"] = dr
    df["kat"] = kt

    ensure_parent_dir(args.output)
    df.to_csv(args.output, index=False)

if __name__ == "__main__":
    main()
