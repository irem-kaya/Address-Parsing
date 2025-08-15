# addresskit/scoring/confidence.py
from __future__ import annotations
import math
import re
from typing import Optional


def extract_numbers(s: str) -> set[str]:
    return set(re.findall(r"\d+", s or ""))


def digits_score(left: str, right: str) -> float:
    """Kapı/bina no gibi rakamlar kesişiyorsa 100, değilse 0. Rakam yoksa 0."""
    L, R = extract_numbers(left), extract_numbers(right)
    if not L or not R:
        return 0.0
    return 100.0 if (L & R) else 0.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def geo_score_km(distance_km: Optional[float], max_km: float = 1.5) -> float:
    """0 km -> 100, max_km ve üstü -> 0, arasında lineer azalsın."""
    if distance_km is None:
        return 0.0
    d = max(0.0, min(distance_km, max_km))
    return 100.0 * (1.0 - d / max_km)


def combine_scores(
    text_score: float,
    digits: float | None = None,
    geo: float | None = None,
    w_text: float = 0.8,
    w_digits: float = 0.2,
    w_geo: float = 0.2,
) -> float:
    parts, weights = [], []
    parts.append(text_score)
    weights.append(w_text)
    if digits is not None:
        parts.append(digits)
        weights.append(w_digits)
    if geo is not None:
        parts.append(geo)
        weights.append(w_geo)
    # aktif ağırlıkları normalize et
    total = sum(weights) if weights else 1.0
    weights = [w / total for w in weights]
    return round(sum(p * w for p, w in zip(parts, weights)), 2)
