# -*- coding: utf-8 -*-
import re
from typing import Dict, Tuple, List

IL_SET = {
    "adana","adiyaman","afyonkarahisar","ağrı","amasya","ankara","antalya","artvin","aydın","aydin",
    "balıkesir","bilecik","bingöl","bitlis","bolu","burdur","bursa","çanakkale","canakkale","çankırı",
    "cankiri","çorum","corum","denizli","diyarbakır","diyarbakir","edirne","elazığ","elazig","erzincan",
    "erzurum","eskişehir","eskisehir","gaziantep","giresun","gümüşhane","gumushane","hakkari","hatay",
    "ısparta","isparta","mersin","istanbul","izmir","kars","kastamonu","kayseri","kırklareli","kirklareli",
    "kırşehir","kirsehir","kocaeli","konya","kütahya","kutahya","malatya","manisa","kahramanmaraş",
    "kahramanmaras","mardin","muğla","mugla","muş","mus","nevşehir","nevsehir","niğde","nigde","ordu",
    "rize","sakarya","samsun","siirt","sinop","sivas","tekirdağ","tekirdag","tokat","trabzon","tunceli",
    "şanlıurfa","sanliurfa","uşak","usak","van","yalova","yozgat","zonguldak","karabük","karabuk","kilis",
    "osmaniye","düzce","duzce","bayburt","ardahan","iğdır","igdir","karaman","kırıkkale","kirikkale","bartın","bartin"
}

TRIGGERS_BUILDING = {"apartman","residence","rezidans","işhanı","işhanı","iş","hanı","otel","hotel","site","blok","plaza","tower"}
CUT_WORDS = {"no","daire","kat","mevkii","il","ilçe","ilce"}

RE_NO = re.compile(r"\bno\s+(\d+[a-z]?(?:/\d+)?[a-z]?)\b", re.IGNORECASE)

def _tokens(s: str) -> List[str]:
    return s.split()

def _get_before_after(label: str, toks: List[str], max_tokens=3, allow_numeric=False) -> Tuple[str,str]:
    if label not in toks: return "", ""
    i = toks.index(label)
    # before
    b = []
    j = i-1
    while j >= 0 and len(b) < max_tokens:
        w = toks[j]
        if w in CUT_WORDS or w in {"mahalle","cadde","sokak","bulvar"}: break
        if not allow_numeric and any(ch.isdigit() for ch in w): break
        b.append(w); j -= 1
    b = " ".join(reversed(b)).strip()
    # after
    a = []
    k = i+1
    while k < len(toks) and len(a) < max_tokens:
        w = toks[k]
        if w in CUT_WORDS or w in {"mahalle","cadde","sokak","bulvar"}: break
        if not allow_numeric and any(ch.isdigit() for ch in w): break
        a.append(w); k += 1
    a = " ".join(a).strip()
    return b, a

def _fix_no_and_daire(parts: Dict[str,str]) -> None:
    if "no" in parts and "/" in parts["no"]:
        n, d = parts["no"].split("/", 1)
        if n.isdigit() and d.isdigit():
            parts["no"], parts["daire"] = n, d
    # alfabetik 'daire' değerlerini kaldır (örn. 'oria')
    if "daire" in parts and not re.fullmatch(r"\d+[a-z]?", str(parts["daire"])):
        parts.pop("daire", None)

def _fix_kat(parts: Dict[str,str]) -> None:
    if "kat" in parts and not re.fullmatch(r"\d+[a-z]?", str(parts["kat"])):
        parts.pop("kat", None)

def _fix_sokak(normalized: str, parts: Dict[str,str]) -> None:
    val = parts.get("sokak","")
    if val.startswith("no"):
        m = re.search(r"\b(\d+)\s+sokak\b", normalized)
        if m: parts["sokak"] = m.group(1)
        else: parts.pop("sokak", None)

def _reassign_mahalle_cadde_sokak(normalized: str, parts: Dict[str,str]) -> None:
    toks = _tokens(normalized)
    # mahalle
    b,a = _get_before_after("mahalle", toks, allow_numeric=False)
    if b: parts["mahalle"] = b
    elif a: parts["mahalle"] = a
    # cadde
    b,a = _get_before_after("cadde", toks, allow_numeric=False)
    if b: parts["cadde"] = b
    elif a: parts["cadde"] = a
    # sokak
    b,a = _get_before_after("sokak", toks, allow_numeric=True)
    if b and b.replace("/","").isdigit():
        parts["sokak"] = b
    elif a and not any(ch.isdigit() for ch in a.split()[:1]):
        parts["sokak"] = a

def _fix_building_name(normalized: str, parts: Dict[str,str]) -> None:
    toks = _tokens(normalized)
    for i, t in enumerate(toks):
        if t in TRIGGERS_BUILDING:
            name_tokens = []
            for j in range(i-2, i):
                if j >= 0 and re.fullmatch(r"[a-zçğıöşü\-]+", toks[j]) and toks[j] not in CUT_WORDS:
                    name_tokens.append(toks[j])
            name_tokens.append(t)
            cand = " ".join(name_tokens).strip()
            # baştaki 'no/sayı' kırp
            cand = re.sub(r"^\bno\b\s*\d+[a-z]?\/?\d*\s*", "", cand).strip()
            cand = re.sub(r"^\d+[a-z]?\s*", "", cand).strip()
            if cand and (parts.get("bina_adı") in (None, "", t) or parts.get("bina_adı","").startswith(("no","0","1","2","3","4","5","6","7","8","9"))):
                parts["bina_adı"] = cand
            break

def _fix_mevkii(normalized: str, parts: Dict[str,str]) -> None:
    m = re.search(r"\b([a-zçğıöşü\-]+)\s+mevkii\b", normalized)
    if m:
        parts["mevkii"] = m.group(1)

def _parse_city_district_from_tail(normalized: str, parts: Dict[str,str]) -> None:
    toks = _tokens(normalized)
    tail = toks[-8:]
    for w in reversed(tail):
        if "/" in w and re.fullmatch(r"[a-zçğıöşü]+/[a-zçğıöşü]+", w):
            a,b = w.split("/",1)
            if b in IL_SET and a not in IL_SET:
                parts["il"], parts["ilçe"] = b, a; return
            if a in IL_SET and b not in IL_SET:
                parts["il"], parts["ilçe"] = a, b; return
    for k in range(len(tail)-1, 0, -1):
        a, b = tail[k-1], tail[k]
        if re.fullmatch(r"[a-zçğıöşü]+", a) and re.fullmatch(r"[a-zçğıöşü]+", b):
            if b in IL_SET and a not in IL_SET:
                parts["il"], parts["ilçe"] = b, a; return

def _recompute_confidence(parts: Dict[str,str]) -> None:
    score = 0.0
    base = ["mahalle","cadde","sokak","no"]
    score += 0.22 * sum(k in parts for k in base)
    if "daire" in parts: score += 0.06
    if "kat"   in parts: score += 0.06
    if "bina_adı" in parts or "mevkii" in parts: score += 0.06
    if "il" in parts: score += 0.06
    parts["_confidence"] = round(min(1.0, score), 2)

def postprocess_parts(normalized: str, parts: Dict[str,str]) -> Dict[str,str]:
    parts = dict(parts)  # kopya
    _fix_no_and_daire(parts)
    _fix_kat(parts)
    _fix_sokak(normalized, parts)
    _reassign_mahalle_cadde_sokak(normalized, parts)
    _fix_building_name(normalized, parts)
    _fix_mevkii(normalized, parts)
    _parse_city_district_from_tail(normalized, parts)
    # alan içi temizlik
    for key in ("mahalle","cadde","sokak"):
        if key in parts and parts[key]:
            parts[key] = re.sub(r"\bno\b.*$", "", parts[key]).strip()
            parts[key] = re.sub(r"\s{2,}", " ", parts[key])
    _recompute_confidence(parts)
    return {k:v for k,v in parts.items() if v}
