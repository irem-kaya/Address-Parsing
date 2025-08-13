"""
Matching module for address data.
"""

from pathlib import Path
import argparse
import csv
import io
import unicodedata
import yaml
from rapidfuzz import fuzz


# ---------- helpers ----------
def _open_read_text(path: str | Path):
    """Bytes -> text: UTF-8-SIG (BOM'u söker) -> UTF-8 -> cp1254."""
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


def tr_safe_lower(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u0130", "I").replace("\u0307", "")  # İ ve combining dot
    s = s.lower()
    return unicodedata.normalize("NFC", s)


def pick_text_col(row: dict) -> str:
    # önce normalize edilmiş kolonu tercih et
    if "address_norm" in row:
        return "address_norm"
    if "address" in row:
        return "address"
    # değilse ilk str alan
    for k, v in row.items():
        if isinstance(v, str):
            return k
    # çaresiz: ilk anahtar
    return next(iter(row.keys()))


def _make_block_key(row: dict, text_col: str, strategy: str) -> str:
    """Basit blok anahtarı üretimi."""
    if not strategy:
        return "__ALL__"
    strategy = strategy.strip().lower()
    if strategy == "first_token":
        tokens = (row.get(text_col) or "").split()
        return tokens[0] if tokens else ""
    # örn: "city" / "district" gibi bir kolon adı verilmişse
    return (row.get(strategy) or "").strip()


# ---------- core ----------
def match_addresses(left_path, right_path, output_path, config_path):
    cfg = load_cfg(config_path)

    method = str(cfg.get("method", "fuzzy")).lower()  # "index" ya da "fuzzy"
    left_id = cfg.get("left_id", "id")
    right_id = cfg.get("right_id", "id")

    # threshold: 0-100 beklenir; 0-1 verilirse yüzdeye çevir
    raw_thr = cfg.get("threshold", 80)
    try:
        thr = float(raw_thr)
        if thr <= 1.0:
            thr *= 100.0
    except Exception:
        thr = 80.0

    # bloklama stratejisi (None/"first_token"/kolon_adi)
    block_by = cfg.get("block_by")
    # unmatched dosyaları
    write_unmatched = bool(cfg.get("write_unmatched", False))
    unmatched_left_path = cfg.get("unmatched_left", "data/processed/unmatched_left.csv")
    unmatched_right_path = cfg.get(
        "unmatched_right", "data/processed/unmatched_right.csv"
    )

    left_rows = list(csv.DictReader(_open_read_text(left_path)))
    right_rows = list(csv.DictReader(_open_read_text(right_path)))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ---- index mode: testler için birebir eşle (score=1.0) ----
    if method == "index":
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"])
            w.writeheader()
            n = min(len(left_rows), len(right_rows))
            for i in range(n):
                lid = left_rows[i].get(left_id, str(i))
                rid = right_rows[i].get(right_id, str(i))
                w.writerow({"left_id": lid, "right_id": rid, "score": 1.0})
        print(f"[match] wrote -> {out}  (config={config_path}, method=index)")
        return

    # ---- fuzzy mode: rapidfuzz ile en iyi eşiği yaz ----
    if not left_rows or not right_rows:
        # yine de boş csv üretelim
        with out.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"]).writeheader()
        print(f"[match] no data -> {out} (config={config_path})")
        return

    # kolon seç (adres metni için)
    text_col_cfg = cfg.get("text_col")
    l_text_col = text_col_cfg or pick_text_col(left_rows[0])
    r_text_col = text_col_cfg or pick_text_col(right_rows[0])

    # skorlayıcı seç
    scorer_name = str(cfg.get("scorer", "token_set_ratio")).lower()
    scorers = {
        "token_set_ratio": fuzz.token_set_ratio,
        "ratio": fuzz.ratio,
        "partial_ratio": fuzz.partial_ratio,
    }
    scorer = scorers.get(scorer_name, fuzz.token_set_ratio)

    # TR-güvenli normalize (metin kolonları üzerinde)
    for r in left_rows:
        r[l_text_col] = tr_safe_lower(r.get(l_text_col, ""))
    for r in right_rows:
        r[r_text_col] = tr_safe_lower(r.get(r_text_col, ""))

    # Sağ tarafı bloklara ayır (lookup hız için)
    right_blocks: dict[str, list[dict]] = {"__ALL__": right_rows}
    if block_by:
        right_blocks = {}
        for rr in right_rows:
            key = _make_block_key(rr, r_text_col, block_by)
            right_blocks.setdefault(key, []).append(rr)

    matches: list[dict] = []
    matched_left_ids = set()
    matched_right_ids = set()

    # brute-force en iyi eşleşme (blok içinde)
    for i, lrow in enumerate(left_rows):
        ltxt = lrow.get(l_text_col, "")
        lid_val = lrow.get(left_id, str(i))

        # blok anahtarı ve adaylar
        if block_by:
            key = _make_block_key(lrow, l_text_col, block_by)
            candidates = right_blocks.get(key, [])
        else:
            candidates = right_rows

        best_score = -1.0
        best_rid_val = None

        for j, rrow in enumerate(candidates):
            rid_val = rrow.get(right_id, "")
            score = float(scorer(ltxt, rrow.get(r_text_col, "")))
            if score > best_score:
                best_score = score
                best_rid_val = rid_val

        if best_score >= thr and best_rid_val is not None:
            matches.append(
                {
                    "left_id": lid_val,
                    "right_id": best_rid_val,
                    "score": round(best_score, 2),
                }
            )
            matched_left_ids.add(lid_val)
            matched_right_ids.add(best_rid_val)

    # yaz: eşleşmeler
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"])
        w.writeheader()
        for m in matches:
            w.writerow(m)

    # yaz: unmatched (opsiyonel)
    if write_unmatched:
        # left tarafı dump
        try:
            upath = Path(unmatched_left_path)
            upath.parent.mkdir(parents=True, exist_ok=True)
            with upath.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=[left_id, "address", "address_norm"])
                w.writeheader()
                for i, lrow in enumerate(left_rows):
                    lid_val = lrow.get(left_id, str(i))
                    if lid_val not in matched_left_ids:
                        w.writerow(
                            {
                                left_id: lid_val,
                                "address": lrow.get("address", ""),
                                "address_norm": lrow.get(
                                    "address_norm", lrow.get(l_text_col, "")
                                ),
                            }
                        )
        except Exception:
            pass

        # right tarafı dump
        try:
            upath = Path(unmatched_right_path)
            upath.parent.mkdir(parents=True, exist_ok=True)
            with upath.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=[right_id, "address", "address_norm"])
                w.writeheader()
                for j, rrow in enumerate(right_rows):
                    rid_val = rrow.get(right_id, str(j))
                    if rid_val not in matched_right_ids:
                        w.writerow(
                            {
                                right_id: rid_val,
                                "address": rrow.get("address", ""),
                                "address_norm": rrow.get(
                                    "address_norm", rrow.get(r_text_col, "")
                                ),
                            }
                        )
        except Exception:
            pass
        print("[unmatched] left -> unmatched_left.csv, right -> unmatched_right.csv")

    print(
        f"[match] wrote -> {out}  (config={config_path}, method=fuzzy, "
        f"text_col={l_text_col}/{r_text_col}, scorer={scorer_name}, threshold={thr})"
    )


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--left", required=True)
    p.add_argument("--right", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config", required=True)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    match_addresses(args.left, args.right, args.out, args.config)
