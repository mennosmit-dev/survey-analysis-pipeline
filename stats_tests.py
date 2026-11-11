"""Significantietoetsen zonder SciPy: chi-kwadraat (onafhankelijkheid), Mann-Whitney U en Benjamini-Hochberg.

Bewust zelf geschreven met alleen numpy en math, zodat de keten minder afhankelijkheden heeft.
De tests in tests/ controleren de uitkomsten tegen bekende tabelwaarden.
"""
import math

import numpy as np


# --- chi-kwadraatverdeling: rechteroverschrijdingskans via de geregulariseerde onvolledige gammafunctie ---

def _gamma_p_reeks(a: float, x: float) -> float:
    som = term = 1.0 / a
    n = a
    for _ in range(500):
        n += 1
        term *= x / n
        som += term
        if abs(term) < abs(som) * 1e-15:
            break
    return som * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gamma_q_kettingbreuk(a: float, x: float) -> float:
    klein = 1e-300
    b = x + 1 - a
    c = 1 / klein
    d = 1 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = klein if abs(d) < klein else d
        c = b + an / c
        c = klein if abs(c) < klein else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x: float, df: int) -> float:
    """P(X >= x) voor een chi-kwadraatverdeling met df vrijheidsgraden."""
    if x <= 0:
        return 1.0
    a, half = df / 2, x / 2
    if half < a + 1:
        return 1 - _gamma_p_reeks(a, half)
    return _gamma_q_kettingbreuk(a, half)


def chi2_onafhankelijkheid(tabel) -> dict:
    """Chi-kwadraattoets op een kruistabel (rijen x kolommen, aantallen).

    Geeft chi2, df, p, Cramér's V en het aandeel cellen met verwacht aantal < 5 (vuistregel: boven 20%
    is de toets onbetrouwbaar; dan alleen beschrijven)."""
    t = np.asarray(tabel, dtype=float)
    t = t[t.sum(axis=1) > 0][:, t.sum(axis=0) > 0]  # lege rijen/kolommen tellen niet mee
    n = t.sum()
    verwacht = np.outer(t.sum(axis=1), t.sum(axis=0)) / n
    chi2 = float(((t - verwacht) ** 2 / verwacht).sum())
    df = (t.shape[0] - 1) * (t.shape[1] - 1)
    k = min(t.shape) - 1
    return {"chi2": chi2, "df": df, "p": chi2_sf(chi2, df) if df > 0 else 1.0,
            "cramers_v": math.sqrt(chi2 / (n * k)) if k > 0 else 0.0,
            "aandeel_verwacht_onder_5": float((verwacht < 5).mean()), "n": int(n)}


# --- Mann-Whitney U (normale benadering met correctie voor knopen): geschikt voor 1-7 schalen ---

def _rangen(waarden: np.ndarray) -> np.ndarray:
    volgorde = np.argsort(waarden, kind="mergesort")
    rang = np.empty(len(waarden))
    gesorteerd = waarden[volgorde]
    i = 0
    while i < len(waarden):
        j = i
        while j + 1 < len(waarden) and gesorteerd[j + 1] == gesorteerd[i]:
            j += 1
        rang[volgorde[i:j + 1]] = (i + j) / 2 + 1  # gemiddelde rang bij gelijke waarden
        i = j + 1
    return rang


def mann_whitney(a, b) -> dict:
    """Tweezijdige Mann-Whitney U-toets. Effectgrootte: rank-biserial r (-1 tot 1, positief = a hoger)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return {"U": None, "z": None, "p": None, "r": None, "n1": n1, "n2": n2}
    alles = np.concatenate([a, b])
    rang = _rangen(alles)
    u1 = rang[:n1].sum() - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    _, aantallen = np.unique(alles, return_counts=True)
    n = n1 + n2
    knopen = (aantallen ** 3 - aantallen).sum()
    sigma = math.sqrt(n1 * n2 / 12 * ((n + 1) - knopen / (n * (n - 1))))
    if sigma == 0:
        return {"U": u1, "z": 0.0, "p": 1.0, "r": 0.0, "n1": n1, "n2": n2}
    z = (u1 - mu - math.copysign(0.5, u1 - mu)) / sigma if u1 != mu else 0.0  # continuïteitscorrectie
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"U": float(u1), "z": z, "p": min(1.0, p), "r": 2 * u1 / (n1 * n2) - 1, "n1": n1, "n2": n2}


def benjamini_hochberg(pwaarden) -> list:
    """Gecorrigeerde p-waarden (false discovery rate) bij veel toetsen tegelijk. None blijft None."""
    geldig = [(i, p) for i, p in enumerate(pwaarden) if p is not None]
    m = len(geldig)
    uit = [None] * len(pwaarden)
    vorige = 1.0
    for rang, (i, p) in reversed(list(enumerate(sorted(geldig, key=lambda x: x[1]), start=1))):
        vorige = min(vorige, p * m / rang)
        uit[i] = vorige
    return uit
