<<<<<<< HEAD
import unicodedata
from typing import Dict, Tuple
=======
>>>>>>> irem/main
import regex as re

def normalize_text(text, cfg):
    """
    Normalize address text:
    - lowercasing
    - punctuation removal
    - abbreviation expansion
    """
    text = text.lower()

    # Noktalama işaretlerini boşluk yap
    if cfg.get("strip_punct", False):
        text = re.sub(r"[^\w\s]", " ", text)

    tokens = text.split()
    new_tokens = []

    for tok in tokens:
        replaced = False
        for canon, variants in cfg.get("expand_abbr", {}).items():
            if tok in variants or tok == canon:
                new_tokens.append(canon)
                replaced = True
                break
        if not replaced:
            new_tokens.append(tok)

    return " ".join(new_tokens), None


def extract_parts(text, cfg):
    """
    Extract parts (no, kat, daire, mahalle, sokak...) using regex rules.
    """
    parts = {}
    for key, pattern in cfg.get("parts", {}).items():
        m = re.search(pattern, text)
        if m:
<<<<<<< HEAD
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
            parts[key] = m.group(1).strip()
    return parts
>>>>>>> irem/main
