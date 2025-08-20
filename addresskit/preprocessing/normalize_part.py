# addresskit/preprocessing/normalize_part.py
# -*- coding: utf-8 -*-
import re

# --- lowercase (TR) ---
def tr_lower(s: str) -> str:
    return str(s).replace("I", "ı").replace("İ", "i").lower()

# --- kısaltmalar ve standartlaştırma eşlemleri ---
ABBR_MAP = {
    r"\bmah\.?\b": "mahalle",
    r"\bmahallesi\b": "mahalle",
    r"\bmh\.?\b": "mahalle",
    r"\bcd\.?\b": "cadde",
    r"\bcad\.?\b": "cadde",
    r"\bcaddesi\b": "cadde",
    r"\bbulv?\.?\b": "bulvar",
    r"\bsok\.?\b": "sokak",
    r"\bsk\.?\b": "sokak",
    r"\bsokağı\b": "sokak",
    r"\bno[:\.]?\b": "no",
    r"\bd[:\.]?\b": "daire",
    r"\bk[:\.]?\b": "kat",
    r"\bap?t\.?\b": "apartman",
}

# sınır/boundary anahtarları
BOUNDARY_WORDS = {
    "mahalle", "cadde", "sokak", "bulvar", "no", "daire", "kat",
    "mevkii", "apartman", "apt", "site", "blok",
    "il", "ilçe", "ilce", "bina", "residence", "rezidans",
    "otel", "hotel", "plaza", "tower", "işhanı", "işhanı"
}

# bina adı tetikleyicileri
BUILDING_TRIGGERS = {"apartman", "apt", "residence", "rezidans", "site", "blok", "plaza", "tower", "işhanı", "işhanı"}

# sık kullanılan iller (kısa liste; istersen genişlet)
IL_SET = {
    "adana","adiyaman","afyonkarahisar","ağrı","amasya","ankara","antalya","artvin","aydin","aydın","balıkesir",
    "bilecik","bingöl","bitlis","bolu","burdur","bursa","çanakkale","canakkale","çankırı","cankiri","çorum","corum",
    "denizli","diyarbakır","diyarbakir","edirne","elazığ","elazig","erzincan","erzurum","eskişehir","eskisehir",
    "gaziantep","giresun","gümüşhane","gumushane","hakkari","hatay","ısparta","isparta","mersin","istanbul","izmir",
    "kars","kastamonu","kayseri","kırklareli","kirklareli","kırşehir","kirsehir","kocaeli","konya","kütahya","kutahya",
    "malatya","manisa","kahramanmaraş","kahramanmaras","mardin","muğla","mugla","muş","mus","nevşehir","nevsehir",
    "niğde","nigde","ordu","rize","sakarya","samsun","siirt","sinop","sivas","tekirdağ","tekirdag","tokat","trabzon",
    "tunceli","şanlıurfa","sanliurfa","uşak","usak","van","yalova","yozgat","zonguldak","karabük","karabuk","kilis",
    "osmaniye","düzce","duzce","bayburt","ardıhan","ardahan","igdir","iğdır","karaman","kırıkkale","kirikkale","bartın","bartin",
    "gümüşhane","gumushane"
}

def normalize_address(s: str) -> str:
    """Adres metnini normalleştir: TR lower, kısaltma aç, noktalama/boşluk düzelt."""
    s = tr_lower(s)

    # virgül/paren -> boşluk
    s = re.sub(r"[(),]", " ", s)

    # kısaltmaları aç (cad., mh., sk. vb.)
    for pat, rep in ABBR_MAP.items():
        s = re.sub(pat, rep, s)

    # "no:15", "kat:2", "daire.3" -> düzgün boşluk
    s = re.sub(r"\b(no|daire|kat)\s*[:\.]?\s*", r"\1 ", s)

    # 90A -> 90a
    s = re.sub(r"([0-9]+)([a-z])", lambda m: f"{m.group(1)}{m.group(2)}", s)

    # Sayılar arasındaki / kalsın (10/3), diğer tüm / boşluğa (fethiye/muğla -> fethiye muğla)
    s = re.sub(r"(?<!\d)/(?!\d)", " ", s)

    # kalan noktaları ve gereksiz noktalama işaretlerini temizle
    s = re.sub(r"[\.]", " ", s)
    s = re.sub(r"[;:!?]", " ", s)

    # çoklu boşlukları sıkıştır
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str):
    return s.split()

def _is_number_token(t: str) -> bool:
    # 2001, 90a, 10/3 gibi
    return re.fullmatch(r"\d+(?:/\d+)?[a-z]?", t) is not None

def _split_no_daire(token: str):
    """10/3 → (10, 3); 10 → (10, None)"""
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", token)
    if m:
        return m.group(1), m.group(2)
    m2 = re.fullmatch(r"(\d+[a-z]?)", token)
    if m2:
        return m2.group(1), None
    return None, None

def _extract_il_ilce_from_tail(tokens):
    """Sondaki 8 token içinden il/ilçe yakala: 'fethiye/muğla' veya 'fethiye muğla'."""
    il = ilce = None
    tail = tokens[-8:] if len(tokens) >= 8 else tokens[:]
    # önce slashlı
    for t in reversed(tail):
        if "/" in t:
            a, b = [x.strip() for x in t.split("/", 1)]
            a_ok, b_ok = a in IL_SET, b in IL_SET
            if a_ok and not b_ok:
                il, ilce = a, ilce or b
                break
            if b_ok and not a_ok:
                il, ilce = b, ilce or a
                break
    # sonra boşlukla ardışık (… fethiye muğla)
    if il is None:
        for i in range(len(tail) - 1, 0, -1):
            if tail[i] in IL_SET and tail[i-1] not in IL_SET and not _is_number_token(tail[i-1]):
                il, ilce = tail[i], ilce or tail[i-1]
                break
    return il, ilce

def extract_parts(addr_norm: str):
    """Anahtar bazlı parça çıkarımı + ek kurallar: il/ilçe, apartman/bina_adı, mevkii, no/daire bölme"""
    toks = tokenize(addr_norm)
    fields = {
        "mahalle": None, "cadde": None, "sokak": None, "bulvar": None,
        "no": None, "daire": None, "kat": None,
        "bina_adı": None, "mevkii": None, "il": None, "ilçe": None
    }

    def _grab_backward_name(idx, key, max_len=3):
        # idx: anahtar kelimenin index'i; geriye doğru 1–3 kelime al
        j = idx - 1
        bucket = []
        while j >= 0 and len(bucket) < max_len:
            tj = toks[j]
            if tj in fields or tj in BOUNDARY_WORDS:
                break
            # sadece SOKAK için sayıya izin ver
            if key != "sokak" and _is_number_token(tj):
                break
            bucket.append(tj)
            j -= 1
        bucket.reverse()
        return " ".join(bucket) if bucket else None

    i, n = 0, len(toks)
    while i < n:
        t = toks[i]

        # numerik alanlar
        if t in {"no", "daire", "kat"}:
            if i + 1 < n:
                candidate = toks[i+1]
                no_val, daire_val = _split_no_daire(candidate)
                if t == "no" and no_val:
                    fields["no"] = no_val
                    if daire_val and not fields["daire"]:
                        fields["daire"] = daire_val
                    i += 2
                    continue
                if t in {"daire","kat"} and _is_number_token(candidate):
                    fields[t] = candidate
                    i += 2
                    continue
            i += 1
            continue

        # isim alanları
        if t in {"mahalle", "cadde", "sokak", "bulvar"}:
            key = t

            # geri bakış
            back_val = _grab_backward_name(i, key, max_len=3)

            # ileri bakış
            j = i + 1
            fwd_bucket = []
            while j < n:
                tj = toks[j]
                if tj in fields or tj in BOUNDARY_WORDS:
                    break
                # yalnızca SOKAK için sayıya izin ver
                if key != "sokak" and _is_number_token(tj):
                    break
                fwd_bucket.append(tj)
                if len(fwd_bucket) >= 3:
                    break
                j += 1
            fwd_val = " ".join(fwd_bucket) if fwd_bucket else None

            # özel: "2001 sokak" → sokak=2001
            if key == "sokak" and not back_val and not fwd_val and i > 0 and _is_number_token(toks[i-1]):
                back_val = toks[i-1]

            val = back_val or fwd_val
            if val:
                fields[key] = val
            i = j if fwd_val else i + 1
            continue

        # mevkii (X mevkii)
        if t == "mevkii":
            # geri bak 1–3 kelime
            name = _grab_backward_name(i, key="mevkii", max_len=3)
            if name:
                fields["mevkii"] = name
            i += 1
            continue

        # bina_adı tetikleyicileri: önceki 1–3 kelimeyi al
        if t in BUILDING_TRIGGERS:
            name = _grab_backward_name(i, key="bina", max_len=3)
            if name:
                fields["bina_adı"] = (name + " " + t).strip()
            else:
                fields["bina_adı"] = t
            i += 1
            continue

        i += 1

    # il/ilçe: sondan çıkar
    il, ilce = _extract_il_ilce_from_tail(toks)
    if il: fields["il"] = il
    if ilce: fields["ilçe"] = ilce

    # none'ları at
    parts = {k: v for k, v in fields.items() if v}

    # basit güven skoru
    need = ["mahalle","cadde","sokak","no"]
    hit = sum(k in parts for k in need)
    score = 0.2 * hit
    if "il"   in parts: score += 0.1
    if "ilçe" in parts: score += 0.1
    if "daire" in parts: score += 0.1
    if "bina_adı" in parts: score += 0.1
    parts["_confidence"] = min(1.0, round(score, 2))

    return parts

def normalize_and_parse(s: str):
    """Kombine yardımcı: normalize et + parçaları çıkar."""
    norm = normalize_address(s)
    parts = extract_parts(norm)
    return norm, parts

__all__ = [
    "normalize_address",
    "extract_parts",
    "normalize_and_parse"
]
