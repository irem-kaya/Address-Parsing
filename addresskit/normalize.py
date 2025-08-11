"""
Normalize module for address processing.
"""
from pathlib import Path
import argparse
import csv
import unicodedata
import io

def _open_read_text(path: Path):
    """Bytes -> text: önce UTF-8, olmazsa cp1254 (Windows Türkçe)."""
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1254")
    return io.StringIO(text)  # file-like object

def tr_safe_lower(s: str) -> str:
    if not s:
        return s
    s = s.replace("\u0130", "I")  # İ -> I
    s = s.replace("\u0307", "")   # combining dot
    s = s.lower()
    return unicodedata.normalize("NFC", s)

def normalize_text(addr: str) -> str:
    addr = tr_safe_lower(addr)
    return " ".join(addr.split())

def normalize_address(input_path, output_path, config_path):
    src = Path(input_path)
    dst = Path(output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with _open_read_text(src) as f_in, dst.open("w", encoding="utf-8", newline="") as f_out:
        r = csv.DictReader(f_in)
        fieldnames = r.fieldnames or []
        if "address" in fieldnames and "address_norm" not in fieldnames:
            fieldnames = fieldnames + ["address_norm"]
        elif "address" not in fieldnames:
            fieldnames = ["address", "address_norm"]

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
