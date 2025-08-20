import re

# --- 1) Normalizasyon (TR lower + kısaltmalar) ---
def tr_lower(s: str):
    return s.replace("I","ı").replace("İ","i").lower()

ABBR_MAP = {
    r"\bmah\.?\b": "mahalle",
    r"\bmahallesi\b": "mahalle",
    r"\bcd\.?\b": "cadde",
    r"\bcaddesi\b": "cadde",
    r"\bsok\.?\b": "sokak",
    r"\bsk\.?\b": "sokak",
    r"\bsokağı\b": "sokak",
    r"\bno[:\.]?\b": "no",
    r"\bd[:\.]?\b": "daire",
    r"\bk[:\.]?\b": "kat",
}

BOUNDARY_WORDS = {
    "mahalle","cadde","sokak","no","daire","kat",
    "mevkii","apartman","apt","site","blok","il","ilçe","ilce","bina",
    "foto","otel","hotel","residence","residans","şehir","sehir","şehr","seh"
}

def normalize_address(s: str) -> str:
    s = tr_lower(str(s))
    # Noktaları tamamen silmeyelim; 10/3 gibi yapıları koru, "864.sok" -> "864 sokak" zaten ABBR_MAP ile düzeliyor
    s = re.sub(r"[\,]", " ", s)          # virgül -> boşluk
    s = re.sub(r"[()]", " ", s)
    # kısaltmaları aç
    for pat, rep in ABBR_MAP.items():
        s = re.sub(pat, rep, s)
    # no 15 → "no 15" benzeri
    s = re.sub(r"no\s*[:\.]?\s*", "no ", s)
    s = re.sub(r"daire\s*[:\.]?\s*", "daire ", s)
    s = re.sub(r"kat\s*[:\.]?\s*", "kat ", s)
    # harf-sayı karışımı 90A -> 90a
    s = re.sub(r"([0-9]+)([a-z])", lambda m: f"{m.group(1)}{m.group(2)}", s)
    # çoklu boşlukları sıkıştır
    s = re.sub(r"\s+", " ", s).strip()
    return s

# --- 2) Anahtar tabanlı parça çıkarımı ---
def tokenize(s: str):
    # basit boşluk bölme; / ve . içeren 10/3 gibi yapılar kalsın
    # nokta çoğu yerde anlamlı değilse boşluğa çevrilmiş durumda
    return s.split()

def extract_parts(addr_norm: str):
    toks = tokenize(addr_norm)
    parts = {"mahalle": None, "cadde": None, "sokak": None, "no": None, "daire": None, "kat": None}
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in parts:
            j = i + 1
            bucket = []
            while j < len(toks):
                tj = toks[j]
                # durdurma koşulları
                if tj in parts or tj in BOUNDARY_WORDS:
                    break
                # sayı geldi ve alan mahalle/cadde/sokak ise: 
                # genelde numara sonraki alanın başlangıcıdır (örn 2001 sokak → sayıyı sokak adı olarak alma)
                if t in {"mahalle","cadde","sokak"} and re.fullmatch(r"\d+[a-z]?", tj):
                    break
                bucket.append(tj)
                # çok uzun kaçmasın; sokak/mahalle isimleri genelde 1–3 kelime
                if t in {"mahalle","cadde","sokak"} and len(bucket) >= 3:
                    # Eğer sonraki token boundary değilse 3 kelime ile yetin
                    pass
                j += 1
            val = " ".join(bucket).strip() if bucket else None

            # özel alanlar: no/daire/kat tek token (numara veya 10/3 gibi)
            if t in {"no","daire","kat"}:
                if j < len(toks):
                    nxt = toks[j]
                else:
                    nxt = None
                # no sonrası doğrudan sayı/10/3/90a gibi
                if nxt and re.fullmatch(r"\d+[\/]?\d*[a-z]?", nxt):
                    val = nxt
                    j = j + 1  # bir token tükettik
                # aksi halde boş bırak

            if val:
                parts[t] = val

            i = j
            continue

        i += 1

    # None'ları sil
    parts = {k:v for k,v in parts.items() if v}
    return parts
