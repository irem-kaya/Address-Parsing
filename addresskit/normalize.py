"""
Normalize module for address processing.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import io
import re
import unicodedata
import yaml


# --------------------------------
# I/O helpers
# --------------------------------
def _open_read_text(path: str | Path):
    """Bytes -> text: UTF-8-SIG -> UTF-8 -> cp1254 fallback."""
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return io.StringIO(data.decode(enc))
        except UnicodeDecodeError:
            pass
    return io.StringIO(data.decode("cp1254"))


def load_cfg(cfg_path: str) -> dict:
    p = Path(cfg_path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


# --------------------------------
# Text helpers
# --------------------------------
def tr_safe_lower(s: str) -> str:
    if not s:
        return s
    s = s.replace("\u0130", "I")  # İ -> I
    s = s.replace("\u0307", "")  # combining dot (ı/İ hassasiyeti)
    s = s.lower()
    return unicodedata.normalize("NFC", s)


def _maybe_unmojibake(s: str) -> str:
    """UTF-8'in latin-1/cp1252 gibi yanlış decode edilmesiyle oluşan 'Ã, Ä, Å' dizilerini düzelt."""
    if not s:
        return s
    if "Ã" in s or "Ä" in s or "Å" in s:
        try:
            return s.encode("latin1").decode("utf-8")
        except Exception:
            return s
    return s


def _fold_tr_diacritics(s: str) -> str:
    """çğışöü (ve büyük halleri) -> c g i s o u  (eşleşmeyi kolaylaştırır)"""
    table = str.maketrans(
        {
            "ç": "c",
            "ğ": "g",
            "ı": "i",
            "ş": "s",
            "ö": "o",
            "ü": "u",
            "Ç": "c",
            "Ğ": "g",
            "İ": "i",
            "Ö": "o",
            "Ş": "s",
            "Ü": "u",
        }
    )
    return s.translate(table)


# --------------------------------
# Core normalize
# --------------------------------
def normalize_text(addr: str, cfg: dict) -> str:
    """YAML konfige göre adım adım normalizasyon uygular."""
    addr = addr or ""

    # 0) Mojibake düzelt (opsiyonel)
    if cfg.get("fix_mojibake", False):
        addr = _maybe_unmojibake(addr)

    # 1) TR-güvenli lowercase
    if cfg.get("lowercase", True):
        addr = tr_safe_lower(addr)

    # 1.5) Diakritik katlama (opsiyonel)
    if cfg.get("fold_diacritics", False):
        addr = _fold_tr_diacritics(addr)

    # 2) Regex kuralları (sırayla)
    for rule in cfg.get("regex") or []:
        try:
            pat = rule.get("pattern")
            repl = rule.get("repl", "")
            if pat:
                addr = re.sub(pat, repl, addr, flags=re.UNICODE)
        except Exception:
            # Bozuk desenleri sessizce atla
            pass

    # 3) Basit replace (literal)
    for k, v in (cfg.get("replace") or {}).items():
        if isinstance(k, str):
            addr = addr.replace(k, v if isinstance(v, str) else "")

    # 4) Kısaltmalar (kelime sınırıyla)
    for src, tgt in (cfg.get("abbreviations") or {}).items():
        if not isinstance(src, str):
            continue
        addr = re.sub(rf"\b{re.escape(src)}\b", str(tgt), addr, flags=re.UNICODE)

    # 5) Stopword temizliği
    stops = set(cfg.get("stopwords") or [])
    if stops:
        addr = " ".join(t for t in addr.split() if t not in stops)

    # 6) Noktalama sadeleştirme (opsiyonel)
    if cfg.get("strip_punctuation", False):
        addr = re.sub(r"[^\w\s]", " ", addr, flags=re.UNICODE)

    # 7) Fazla boşluk
    if cfg.get("strip_extra_spaces", True):
        addr = " ".join(addr.split())

    return addr


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

        # Header temizliği (BOM/boşluk)
        fns = r.fieldnames or []
        fns = [(fn or "").lstrip("\ufeff").strip() for fn in fns]
        r.fieldnames = fns

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
            safe_row = {k: row.get(k, "") for k in out_fields}
            addr = (safe_row.get("address") or "").strip()
            safe_row["address_norm"] = normalize_text(addr, cfg)
            w.writerow(safe_row)

    print(f"[normalize] wrote -> {dst}  (config={config_path})")


# --------------------------------
# CLI
# --------------------------------
def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--config", required=True)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    normalize_address(args.input, args.output, args.config)
