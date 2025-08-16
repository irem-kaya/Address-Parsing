import argparse
<<<<<<< HEAD
from .matching.string_similarity import run_match

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    run_match(args.train, args.test, args.out)
=======

from pathlib import Path
import csv
import io
import unicodedata
import yaml
from rapidfuzz import fuzz

"""
Matching module for address data (blocking + confidence + stopword gating).
"""

# internal modules
from addresskit.matching.blocking import group_by_block
from addresskit.scoring.confidence import (
    digits_score,
    haversine_km,
    geo_score_km,
    combine_scores,
)

# ---------- helpers ----------
def _open_read_text(path: str | Path):
    """Bytes -> text: UTF-8-SIG -> UTF-8 -> cp1254 (Windows TR)."""
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
    # öncelik: normalize kolon, sonra address, sonra ilk string kolon
    if "address_norm" in row:
        return "address_norm"
    if "address" in row:
        return "address"
    for k, v in row.items():
        if isinstance(v, str):
            return k
    return next(iter(row.keys()))


def _get_latlon(row: dict):
    lat_keys = ("lat", "latitude", "enlem")
    lon_keys = ("lon", "lng", "longitude", "boylam")
    lat = lon = None
    for k in lat_keys:
        if k in row:
            try:
                lat = float(row.get(k))
            except Exception:
                pass
    for k in lon_keys:
        if k in row:
            try:
                lon = float(row.get(k))
            except Exception:
                pass
    return lat, lon


def _tokenize_without_stops(text: str, stops: set[str]) -> set[str]:
    if not text:
        return set()
    return {t for t in text.split() if t and (t not in stops)}


# ---------- core ----------
def match_addresses(left_path, right_path, output_path, config_path):
    cfg = load_cfg(config_path)

    method = str(cfg.get("method", "fuzzy")).lower()  # "index" | "fuzzy"
    left_id = cfg.get("left_id", "id")
    right_id = cfg.get("right_id", "id")

    # threshold: 0-100; 0-1 verilirse %'ye çevir
    raw_thr = cfg.get("threshold", 80)
    try:
        thr = float(raw_thr)
        if thr <= 1.0:
            thr *= 100.0
    except Exception:
        thr = 80.0

    topk = int(cfg.get("topk", 1))
    block_by = cfg.get("block_by", "")
    write_unmatched = bool(cfg.get("write_unmatched", True))

    # scorer
    scorer_name = str(cfg.get("scorer", "token_set_ratio")).lower()
    scorers = {
        "token_set_ratio": fuzz.token_set_ratio,
        "ratio": fuzz.ratio,
        "partial_ratio": fuzz.partial_ratio,
    }
    scorer = scorers.get(scorer_name, fuzz.token_set_ratio)

    # weights for confidence
    wcfg = cfg.get("weights") or {}
    w_text = float(wcfg.get("text", 0.8))
    w_digits = float(wcfg.get("digits", 0.2))
    w_geo = float(wcfg.get("geo", 0.2))
    max_km = float(cfg.get("geo_max_km", 1.5))

    # semantic stopwords
    stops = set(
        t.strip()
        for t in (cfg.get("semantic_stopwords") or [])
        if t and isinstance(t, str)
    )

    left_rows = list(csv.DictReader(_open_read_text(left_path)))
    right_rows = list(csv.DictReader(_open_read_text(right_path)))

    # boş veri koruması
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not left_rows or not right_rows:
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"])
            w.writeheader()
        print(f"[match] no data -> {out} (config={config_path})")
        return

    # kolon seçimi ve normalize
    text_col_cfg = cfg.get("text_col")
    l_text_col = text_col_cfg or pick_text_col(left_rows[0])
    r_text_col = text_col_cfg or pick_text_col(right_rows[0])

    for r in left_rows:
        r[l_text_col] = tr_safe_lower(r.get(l_text_col, ""))
    for r in right_rows:
        r[r_text_col] = tr_safe_lower(r.get(r_text_col, ""))

    # --- index mode: birebir
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

    # --- fuzzy + confidence + blocking ---
    Lb = group_by_block(left_rows, l_text_col, block_by)
    Rb = group_by_block(right_rows, r_text_col, block_by)

    matched_left, matched_right = set(), set()

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"])
        w.writeheader()

        for key, lbucket in Lb.items():
            rbucket = Rb.get(key, [])
            if not rbucket:
                continue

            # R ön-hesap
            r_pre = []
            for rr in rbucket:
                rtxt = rr.get(r_text_col, "")
                rlat, rlon = _get_latlon(rr)
                rtok = _tokenize_without_stops(rtxt, stops)
                r_pre.append((rr, rtxt, rtok, rlat, rlon))

            for lrow in lbucket:
                ltxt = lrow.get(l_text_col, "")
                lid_val = lrow.get(left_id, "")
                llat, llon = _get_latlon(lrow)
                ltok = _tokenize_without_stops(ltxt, stops)

                best = []
                for rrow, rtxt, rtok, rlat, rlon in r_pre:
                    if stops and not (ltok & rtok):
                        continue

                    text_s = float(scorer(ltxt, rtxt))
                    d_s = digits_score(ltxt, rtxt)

                    g_km = None
                    if (
                        (llat is not None)
                        and (llon is not None)
                        and (rlat is not None)
                        and (rlon is not None)
                    ):
                        g_km = haversine_km(llat, llon, rlat, rlon)
                    g_s = geo_score_km(g_km, max_km=max_km) if g_km is not None else None

                    conf = combine_scores(
                        text_s, d_s, g_s, w_text=w_text, w_digits=w_digits, w_geo=w_geo
                    )
                    if conf >= thr:
                        best.append((conf, rrow))

                if not best:
                    continue

                # top-k
                best.sort(key=lambda x: x[0], reverse=True)
                for conf, rrow in best[:topk]:
                    rrid = rrow.get(right_id, "")
                    w.writerow(
                        {"left_id": lid_val, "right_id": rrid, "score": round(conf, 2)}
                    )
                    matched_left.add(lid_val)
                    matched_right.add(rrid)

    # --- unmatched (opsiyonel) ---
    if write_unmatched:
        left_un = [r for r in left_rows if r.get(left_id, "") not in matched_left]
        if left_un:
            with (out.parent / "unmatched_left.csv").open(
                "w", encoding="utf-8", newline=""
            ) as f:
                ww = csv.DictWriter(f, fieldnames=[left_id, l_text_col])
                ww.writeheader()
                for r in left_un:
                    ww.writerow(
                        {left_id: r.get(left_id, ""), l_text_col: r.get(l_text_col, "")}
                    )

        right_un = [r for r in right_rows if r.get(right_id, "") not in matched_right]
        if right_un:
            with (out.parent / "unmatched_right.csv").open(
                "w", encoding="utf-8", newline=""
            ) as f:
                ww = csv.DictWriter(f, fieldnames=[right_id, r_text_col])
                ww.writeheader()
                for r in right_un:
                    ww.writerow(
                        {
                            right_id: r.get(right_id, ""),
                            r_text_col: r.get(r_text_col, ""),
                        }
                    )

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


def main():
    args = _parse_args()
    match_addresses(args.left, args.right, args.out, args.config)
>>>>>>> irem/main


if __name__ == "__main__":
    main()
