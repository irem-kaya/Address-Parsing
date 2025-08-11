"""
Normalize module for address processing.
"""
from pathlib import Path
import argparse
import csv
import unicodedata

def _open_read(path):
    """UTF-8 dene; olmazsa Windows Türkçe (cp1254) ile oku."""
    try:
        return open(path, "r", encoding="utf-8")
    except UnicodeDecodeError:
        return open(path, "r", encoding="cp1254")

def tr_safe_lower(s: str) -> str:
    """Türkçedeki noktalı İ sorununu düzeltip lower uygula."""
    if not s:
        return s
    s = s.replace("\u0130", "I")   # İ -> I (sonra lower -> i)
    s = s.replace("\u0307", "")    # combining dot above'ı temizle
    s = s.lower()
    return unicodedata.normalize("NFC", s)

def normalize_text(addr: str) -> str:
    addr = tr_safe_lower(addr)
    return " ".join(addr.split())  # fazla boşlukları tekille

def normalize_address(input_path, output_path, config_path):
    # TODO: Gerçek normalizasyon kuralları config'ten okunacak
    src = Path(input_path)
    dst = Path(output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with _open_read(src) as f_in, dst.open("w", encoding="utf-8", newline="") as f_out:
        r = csv.DictReader(f_in)
        fieldnames = r.fieldnames or []
        if "address" in fieldnames and "address_norm" not in fieldnames:
            fieldnames = fieldnames + ["address_norm"]
        elif "address" not in fieldnames:
            fieldnames = ["address", "address_norm"]  # minimal fallback

        w = csv.DictWriter(f_out, fieldnames=fieldnames)
        w.writeheader()

        for row in r:
            addr = (row.get("address") or "").strip()
            row["address_norm"] = normalize_text(addr)
            w.writerow(row)

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
