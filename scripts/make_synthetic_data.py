# scripts/make_synthetic_data.py
from pathlib import Path
import argparse
import csv
import random
import re

ABBR = [
    (" mahalle", " mh."),
    (" mahalle", " m."),
    (" mahalle", " mah"),
    (" sokak", " sk."),
    (" sokak", " sk"),
    (" sokak", " sok."),
    (" cadde", " cd."),
    (" cadde", " cad."),
    (" cadde", " caddesi"),
]
EN_TR = [
    (" street", " sokak"),
    (" avenue", " cadde"),
    (" st.", " sokak"),
    (" ave.", " cadde"),
]
PUNCT = [",", ".", " / ", " - "]

TR_MIX = [
    ("i", "İ"),
    ("i", "ı"),
    ("ı", "i"),
    ("ş", "s"),
    ("ç", "c"),
    ("ğ", "g"),
    ("ö", "o"),
    ("ü", "u"),
]


def rand_drop_token(addr, p=0.15):
    toks = addr.split()
    if len(toks) > 2 and random.random() < p:
        idx = random.randrange(len(toks))
        toks.pop(idx)
    return " ".join(toks)


def rand_shuffle(addr, p=0.2):
    toks = addr.split()
    if len(toks) > 2 and random.random() < p:
        i, j = random.sample(range(len(toks)), 2)
        toks[i], toks[j] = toks[j], toks[i]
    return " ".join(toks)


def rand_num_variation(addr, p=0.5):
    # no:107 → no107, No. 107, NO 107, vb.
    def repl(m):
        n = m.group(1)
        forms = [
            f"no {n}",
            f"no.{n}",
            f"no.{n}",
            f"no:{n}",
            f"no{n}",
            f"no. {n}",
            f"no : {n}",
        ]
        return random.choice(forms)

    if random.random() < p:
        addr = re.sub(r"\bno[\s\.:]*([0-9]+)\b", repl, addr, flags=re.I)
    return addr


def rand_punct(addr, p=0.4):
    if random.random() < p:
        addr = re.sub(r"\s+", " ", addr)
        addr = addr.replace(" ", random.choice(PUNCT))
    return addr


def rand_abbrev(addr, p=0.5):
    if random.random() < p:
        s, t = random.choice(ABBR)
        addr = addr.replace(s, t)
    return addr


def rand_en_tr(addr, p=0.25):
    if random.random() < p:
        s, t = random.choice(EN_TR)
        addr = addr.replace(s, t)
    return addr


def rand_tr_mix(addr, p=0.3):
    if random.random() < p:
        a, b = random.choice(TR_MIX)
        addr = addr.replace(a, b)
    return addr


def rand_case(addr, p=0.5):
    r = random.random()
    if r < p / 2:
        return addr.upper()
    if r < p:
        return addr.title()
    return addr


def typos(addr, p=0.2):
    # basit karakter silme/ekleme/değiştirme
    if not addr or random.random() >= p:
        return addr
    i = random.randrange(len(addr))
    op = random.choice(["del", "dup", "swap"])
    if op == "del":
        return addr[:i] + addr[i + 1 :]
    if op == "dup":
        return addr[:i] + addr[i] + addr[i:]  # çiftle
    if op == "swap" and i + 1 < len(addr):
        s = list(addr)
        s[i], s[i + 1] = s[i + 1], s[i]
        return "".join(s)
    return addr


def perturb(a: str) -> str:
    a = " " + a.strip().lower() + " "  # baş/son kolay replace için
    a = rand_abbrev(a)
    a = rand_en_tr(a)
    a = rand_tr_mix(a)
    a = rand_num_variation(a)
    a = rand_punct(a)
    a = rand_shuffle(a)
    a = rand_drop_token(a)
    a = typos(a)
    a = rand_case(a)
    return " ".join(a.split())


def make_distractor(a: str) -> str:
    # bina no’yu değiştir ya da sokak/cadde’yi başka bir isimle değiştir
    a = re.sub(
        r"\bno[\s\.:]*([0-9]+)\b",
        lambda m: f"no {int(m.group(1))+ random.randint(5,50)}",
        a,
        flags=re.I,
    )
    a = re.sub(
        r"\b(cadde|sokak)\b", lambda m: "bulvar" if m.group(1) == "cadde" else "yol", a
    )
    return perturb(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--left", default="data/raw/left.csv")
    ap.add_argument("--right", default="data/raw/right.csv")
    ap.add_argument("--gt", default="data/external/ground_truth.csv")
    ap.add_argument("--distractors", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)

    left_p = Path(args.left)
    rows = list(csv.DictReader(left_p.open("r", encoding="utf-8-sig")))
    assert (
        "id" in rows[0] and "address" in rows[0]
    ), "left.csv kolonları: id,address olmalı"

    # 1) right adaylarını üret
    right = []
    for r in rows:
        rid = int(r["id"])
        addr = r["address"]
        # %30 hiç dokunma, %70 boz
        noisy = addr if random.random() < 0.30 else perturb(addr)
        right.append({"orig_left_id": rid, "address": noisy})

    # 2) karıştır, yeni right_id ata
    random.shuffle(right)
    for j, r in enumerate(right):
        r["id"] = j

    # 3) distraktör ekle
    for _ in range(args.distractors):
        src = random.choice(rows)["address"]
        right.append(
            {"orig_left_id": None, "address": make_distractor(src), "id": len(right)}
        )

    # 4) yaz: right.csv
    Path(args.right).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.right).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "address"])
        w.writeheader()
        for r in right:
            w.writerow({"id": r["id"], "address": r["address"]})

    # 5) ground_truth: (left_id → doğru right_id)
    gt = []
    # right içinden orig_left_id dolu olanları bularak eşle
    for r in right:
        if r.get("orig_left_id") is not None:
            gt.append({"left_id": r["orig_left_id"], "right_id": r["id"]})

    Path(args.gt).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.gt).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["left_id", "right_id"])
        w.writeheader()
        w.writerows(gt)

    print(
        f"[synthetic] wrote -> {args.right} (+{args.distractors} distr.), gt -> {args.gt}, n_left={len(rows)}, n_right={len(right)}"
    )


if __name__ == "__main__":
    main()
