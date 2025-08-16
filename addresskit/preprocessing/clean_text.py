<<<<<<< HEAD
import unicodedata
from typing import Dict, Tuple
import regex as re

# Regexler
WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\sçğıöşüÇĞİÖŞÜ.-]")  # nokta/tireyi şimdilik koru

def tr_lower(s: str) -> str:
    """Türkçe-safe lower"""
    return (s.replace("I", "ı").replace("İ", "i")).lower()

def strip_punct(s: str) -> str:
    """Noktalama işaretlerini (nokta/tire hariç) boşlukla değiştir"""
    return PUNCT_RE.sub(" ", s)

def collapse_ws(s: str) -> str:
    """Çoklu boşlukları tek boşluğa indir ve baş/son boşlukları sil"""
    return WHITESPACE_RE.sub(" ", s).strip()

def ascii_fold(s: str) -> str:
    """Türkçe karakterleri ASCII karşılığına çevir"""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

def load_config(cfg: Dict) -> Dict:
    """Config dosyasını yükler"""
    return cfg

def expand_abbreviations(s: str, cfg: Dict) -> str:
    """Kısaltmaları genişletir"""
    for canon, alts in cfg.get("expand_abbr", {}).items():
        canon_str = str(canon)  # 🔹 Tip güvenliği
        for a in alts:
            s = re.sub(rf"\b{re.escape(str(a))}\b", canon_str, s)
    return s

def canonicalize_terms(s: str, cfg: Dict) -> str:
    """Terimleri canonical forma çevirir"""
    for raw, canon in cfg.get("canonical_map", {}).items():
        s = re.sub(rf"\b{re.escape(str(raw))}\b", str(canon), s)
    return s

def remove_terms(s: str, cfg: Dict) -> str:
    """Belirli kelimeleri metinden çıkarır"""
    for t in cfg.get("remove_terms", []):
        s = re.sub(rf"\b{re.escape(str(t))}\b", " ", s)
    return s

def normalize_text(text: str, cfg: Dict) -> Tuple[str, str]:
    """
    Adresi normalize eder.
    Dönüş: (primary_norm, secondary_ascii_norm)
    """
    # 🔹 Tip güvenliği: adres string değilse string'e çevir
    if not isinstance(text, str):
        text = "" if text is None else str(text)

    s = text or ""
    if cfg.get("lowercase", True):
        s = tr_lower(s)
    if cfg.get("strip_punct", True):
        s = strip_punct(s)
    s = expand_abbreviations(s, cfg)
    s = canonicalize_terms(s, cfg)
    s = remove_terms(s, cfg)
    if cfg.get("collapse_spaces", True):
        s = collapse_ws(s)

    if cfg.get("ascii_fold_secondary", False):
        s2 = ascii_fold(s)
        s2 = collapse_ws(s2)
    else:
        s2 = s

    return s, s2

def extract_parts(s: str, cfg: Dict) -> Dict[str, str]:
    """
    Regex tabanlı parça çıkarımı
    """
    out = {}
    parts = cfg.get("parts", {})
    for key, pat in parts.items():
        m = re.search(pat, s)
        if m:
            out[key] = collapse_ws(m.group(1))
    # Kapı numarası, daire, kat gibi yaygın parçalar
    if "no" not in out:
        m = re.search(r"\bno\s*([0-9]{1,5}[A-Za-z]?)\b", s)
        if m:
            out["no"] = m.group(1)
    if "daire" not in out:
        m = re.search(r"\bdaire\s*([0-9]{1,5}[A-Za-z]?)\b", s)
        if m:
            out["daire"] = m.group(1)
    if "kat" not in out:
        m = re.search(r"\bkat\s*([0-9]{1,3})\b", s)
        if m:
            out["kat"] = m.group(1)
    return out
=======
import re
import unicodedata
from pathlib import Path
import yaml


def tr_safe_lower(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u0130", "I")  # İ -> I
    s = s.replace("\u0307", "")  # combining dot
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
    for rule in cfg.get("regex") or []:
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
>>>>>>> f3a69242bb20942eb83b5471dc20cc8ed3b34b24
