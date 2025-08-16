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
            parts[key] = m.group(1).strip()
    return parts
