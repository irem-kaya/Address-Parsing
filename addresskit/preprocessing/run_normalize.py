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
