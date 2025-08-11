"""
Normalize module for address processing.
"""
from pathlib import Path
import argparse
import csv
import unicodedata
import io
import yaml  


def _open_read_text(path: Path):
    """Bytes -> text: önce UTF-8-SIG (BOM'u söker), olmazsa UTF-8, en son cp1254."""
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return io.StringIO(data.decode(enc))
        except UnicodeDecodeError:
            pass
    return io.StringIO(data.decode("cp1254"))

def tr_safe_lower(s: str) -> str:
    if not s:
        return s
    s = s.replace("\u0130", "I")  # İ -> I
    s = s.replace("\u0307", "")   # combining dot
    s = s.lower()
    return unicodedata.normalize("NFC", s)

def load_cfg(cfg_path: str) -> dict:
    p = Path(cfg_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def normalize_text(addr: str, cfg: dict) -> str:
    if addr is None:
        addr = ""
    for k, v in (cfg.get("replace") or {}).items():
        addr = addr.replace(k, v)
    if cfg.get("lowercase", True):
        addr = tr_safe_lower(addr)
    if cfg.get("strip_extra_spaces", True):
        addr = " ".join(addr.split())
    return addr

def normalize_address(input_path, output_path, config_path):
    src = Path(input_path)
    dst = Path(output_path)
    cfg = load_cfg(config_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with _open_read_text(src) as f_in, dst.open("w", encoding="utf-8-sig", newline="") as f_out:
        r = csv.DictReader(f_in)

        # Header'ı temizle (BOM/boşluk)
        fns = r.fieldnames or []
        fns = [ (fn or "").lstrip("\ufeff").strip() for fn in fns ]
        r.fieldnames = fns  # DictReader bundan sonra bu isimleri kullanacak

        # Çıkış alanları
        if "address" in r.fieldnames and "address_norm" not in r.fieldnames:
            out_fields = r.fieldnames + ["address_norm"]
        elif "address" not in r.fieldnames:
            out_fields = ["address", "address_norm"]
        else:
            out_fields = r.fieldnames

        w = csv.DictWriter(f_out, fieldnames=out_fields)
        w.writeheader()

        for row in r:
            # Sadece çıkış alanlarını taşı (fazla key -> ValueError engellenir)
            safe_row = {k: row.get(k, "") for k in out_fields}
            addr = (safe_row.get("address") or "").strip()
            safe_row["address_norm"] = normalize_text(addr, cfg)
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
