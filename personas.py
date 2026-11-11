"""Illustratieve persona-indeling. Eigen, bewust eenvoudige regels voor dit voorbeeld; geen gevalideerd model.

Twee assen:
- gebruik:  wekelijks of vaker (frequentiecode 1-3) tegenover minder vaak (4-6)
- houding:  gemiddelde van de "Value"-stellingen (1-7), min de helft van (zorg - 4)

    Champion         wekelijks+   en houding >= 5
    Pragmatist       wekelijks+   en houding <  5
    Curious starter  minder vaak  en houding >= 4
    Sceptic          minder vaak  en houding <  4

Zonder frequentie of zonder Value-scores: geen persona (None), telt niet mee in de verdeling.
"""
from config import STELLINGEN, WEKELIJKS_VANAF


def houding(scores: dict, zorg: int | None) -> float | None:
    waarden = [scores.get(k) for k in STELLINGEN["Value"]]
    waarden = [w for w in waarden if w is not None]
    if not waarden:
        return None
    basis = sum(waarden) / len(waarden)
    return basis - 0.5 * (zorg - 4) if zorg is not None else basis


def persona(freq: int | None, houding_: float | None) -> str | None:
    if freq is None or houding_ is None:
        return None
    if freq <= WEKELIJKS_VANAF:
        return "Champion" if houding_ >= 5 else "Pragmatist"
    return "Curious starter" if houding_ >= 4 else "Sceptic"
