<<<<<<< HEAD
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
=======
from pathlib import Path
import argparse
import csv
import io
from .clean_text import load_cfg, normalize_text, pick_address_col


def _open_read_text(path: Path):
    """Bytes->Text: UTF-8-SIG → UTF-8 → CP1254 (TR)."""
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return io.StringIO(data.decode(enc))
        except UnicodeDecodeError:
            pass
    return io.StringIO(data.decode("cp1254"))


def normalize_address(input_path, output_path, config_path):
    src = Path(input_path)
    dst = Path(output_path)
    cfg = load_cfg(config_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with (
        _open_read_text(src) as f_in,
        dst.open("w", encoding="utf-8", newline="") as f_out,
    ):
        r = csv.DictReader(f_in)
        fns = r.fieldnames or []
        fns = [(fn or "").lstrip("\ufeff").strip() for fn in fns]
        r.fieldnames = fns

        addr_col = pick_address_col(r.fieldnames)

        out_fields = list(r.fieldnames or [])
        if "address_norm" not in out_fields:
            out_fields.append("address_norm")

        w = csv.DictWriter(f_out, fieldnames=out_fields)
        w.writeheader()

        for row in r:
            if not any((v or "").strip() for v in row.values()):
                continue
            safe_row = {k: row.get(k, "") for k in out_fields}
            base = (row.get(addr_col) or "").strip() if addr_col else ""
            safe_row["address_norm"] = normalize_text(base, cfg)
            w.writerow(safe_row)

    print(f"[normalize] wrote -> {dst}  (config={config_path})")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--config", required=True)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    normalize_address(args.input, args.output, args.config)
>>>>>>> f3a69242bb20942eb83b5471dc20cc8ed3b34b24
