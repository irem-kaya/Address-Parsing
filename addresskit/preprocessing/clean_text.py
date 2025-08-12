import re
import unicodedata
from pathlib import Path
import yaml

def tr_safe_lower(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u0130", "I")   # İ -> I
    s = s.replace("\u0307", "")    # combining dot
    s = s.lower()
    return unicodedata.normalize("NFC", s)

def _norm_key(name: str) -> str:
    if not name:
        return ""
    k = tr_safe_lower(name).strip()
    return re.sub(r"[.\s_]+", "", k)  # boşluk/nokta/altçizgi kaldır

def pick_address_col(fieldnames: list[str] | None) -> str | None:
    """'address' yoksa 'adres' vb. varyasyonları yakala; yoksa ilk kolonu seç."""
    if not fieldnames:
        return None
    mapping = {fn: _norm_key(fn) for fn in fieldnames}
    for orig, norm in mapping.items():
        if norm in {"address", "adres", "addressraw", "adresraw"}:
            return orig
    return fieldnames[0]

def load_cfg(cfg_path: str) -> dict:
    p = Path(cfg_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def normalize_text(addr: str, cfg: dict) -> str:
    """YAML konfige göre adım adım normalizasyon uygular."""
    addr = addr or ""

    # bire bir replace
    for k, v in (cfg.get("replace") or {}).items():
        if isinstance(k, str):
            addr = addr.replace(k, v if isinstance(v, str) else "")

    # TR-safe lowercase
    if cfg.get("fold_chars", "tr") == "tr" or cfg.get("lowercase", True):
        addr = tr_safe_lower(addr)
    elif cfg.get("lowercase", False):
        addr = addr.lower()

    # noktalama temizliği
    if cfg.get("strip_punctuation", False):
        addr = re.sub(r"[^\w\s/]", " ", addr, flags=re.UNICODE)

    # regex kuralları
    for rule in (cfg.get("regex") or []):
        pat = rule.get("pattern")
        repl = rule.get("repl", "")
        if pat:
            addr = re.sub(pat, repl, addr)

    # kısaltmalar (kelime sınırı)
    for src, tgt in (cfg.get("abbreviations") or {}).items():
        if isinstance(src, str):
            pattern = rf"\b{re.escape(src.lower())}\b"
            addr = re.sub(pattern, str(tgt), addr, flags=re.UNICODE)

    # stopwords
    stops = set(cfg.get("stopwords") or [])
    if stops:
        addr = " ".join(tok for tok in addr.split() if tok not in stops)

    # fazla boşluk
    if cfg.get("strip_extra_spaces", True):
        addr = " ".join(addr.split())

    return addr
