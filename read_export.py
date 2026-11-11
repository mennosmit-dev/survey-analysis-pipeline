"""Survey-export (CSV of XLSX, Qualtrics-stijl) inlezen en omzetten naar één record per respondent.

De export heeft drie kopregels: kolomcode (Q1, Q6_2, ...), vraagtekst, ImportId. Kolommen worden gekoppeld
op stukjes vraagtekst, niet op kolomcode: codes verschuiven zodra iemand de vragenlijst aanpast.
Klopt een koppeling niet, zet dan de juiste kolom in `data/mapping.json`, bijvoorbeeld {"afdeling": "Q1"}.
De gekozen koppeling staat na elke run in `output/mapping.md`.
"""
import json
import re
import sys

import pandas as pd

from config import (ALLE_STELLINGEN, BARRIERES, DATA, FREQ, GEBRUIKER_VANAF, GEVOELENS, NIET_GEVRAAGD, NIVEAUS,
                    SCHAAL7, TAKEN, ZORG)
from personas import houding, persona

# veld -> stukje vraagtekst (kleine letters)
VELDEN = {
    "afdeling": "which department",
    "freq": "how often do you use ai",
    "taken": "what do you use ai tools for",
    "niveau": "most advanced use",
    "minuten": "minutes per week",
    "gevoel": "how you feel about ai",
    "barrieres": "biggest barriers",
    "wat_helpt": "what would help you",
    "voorbeeld": "one task where ai helped",
    "zorg": ZORG[1].lower(),
} | {k: v.lower() for k, v in ALLE_STELLINGEN.items()}
TEKSTVAKKEN = {"taken_anders": "taken", "barrieres_anders": "barrieres"}  # "Other - Text" bij meerkeuze

FREQ_TEKST = [("several times", 1), ("daily", 2), ("weekly", 3), ("monthly", 4), ("few times a year", 5),
              ("never", 6)]
OPTIES = {"taken": TAKEN, "gevoel": GEVOELENS, "barrieres": BARRIERES}

# Niet nodig voor de analyse en herleidbaar tot personen: meteen bij het inlezen weg
PRIVACYKOLOMMEN = ["IPAddress", "LocationLatitude", "LocationLongitude", "RecipientLastName", "RecipientFirstName",
                   "RecipientEmail", "ExternalReference"]

ONBEKENDE_OPTIES: set[str] = set()  # meerkeuze-antwoorden die bij geen optie passen; run_pipeline meldt ze
ONBEKENDE_LABELS: set[str] = set()  # schaallabels die niet in SCHAAL7 staan


def lees_export(pad) -> tuple[pd.DataFrame, dict]:
    """Geeft de antwoorden (één rij per respondent) en {kolomcode: vraagtekst}."""
    pad = str(pad)
    if pad.lower().endswith((".xlsx", ".xls")):
        ruw = pd.read_excel(pad, header=None, dtype=str)
    else:
        ruw = pd.read_csv(pad, header=None, dtype=str, encoding="utf-8-sig")
    if str(ruw.iloc[1, 0]).startswith("Start Date,"):
        sys.exit("This export was opened and saved in Excel: rows were merged into one column. "
                 "Export again and do not open the CSV in Excel (or export as XLSX).")
    codes, gezien = [], {}
    for c in ruw.iloc[0].tolist():  # een tool kan een code dubbel geven; maak hem uniek
        codes.append(c if c not in gezien else f"{c}.{gezien[c]}")
        gezien[c] = gezien.get(c, 0) + 1
    teksten = {c: t for c, t in zip(codes, ruw.iloc[1].fillna("").tolist()) if c not in PRIVACYKOLOMMEN}
    start = 3 if ruw.iloc[2].fillna("").str.contains("ImportId").any() else 2
    df = ruw.iloc[start:].copy()
    df.columns = codes
    df = df.drop(columns=[c for c in PRIVACYKOLOMMEN if c in df.columns])
    return df.reset_index(drop=True), teksten


def koppel_kolommen(teksten: dict, override_pad=None) -> tuple[dict, list[str]]:
    """Zoekt per veld de kolom op vraagtekst. Geeft de koppeling en een lijst waarschuwingen."""
    override_pad = override_pad or DATA / "mapping.json"
    override = json.loads(override_pad.read_text(encoding="utf-8")) if override_pad.exists() else {}
    koppeling, waarschuwingen = {}, []
    for veld, stuk in VELDEN.items():
        if veld in override:
            koppeling[veld] = override[veld]
            continue
        kandidaten = [c for c, t in teksten.items()
                      if stuk in t.lower() and not str(c).upper().endswith("_TEXT")]
        if not kandidaten:
            waarschuwingen.append(f"No column found for '{veld}' (searching for '{stuk}')")
            continue
        if len(kandidaten) > 1:
            waarschuwingen.append(f"Several columns for '{veld}': {kandidaten}; first one used")
        koppeling[veld] = kandidaten[0]
    for veld, basis in TEKSTVAKKEN.items():
        if veld in override:
            koppeling[veld] = override[veld]
        elif basis in koppeling:
            prefix = str(koppeling[basis]).split("_")[0] + "_"
            tekst = [c for c in teksten if str(c).startswith(prefix) and str(c).upper().endswith("_TEXT")]
            if tekst:
                koppeling[veld] = tekst[0]
    return koppeling, waarschuwingen


def _leeg(x) -> bool:
    """Leeg, NaN of een code voor 'niet gevraagd' tellen allemaal als ontbrekend."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return True
    return str(x).strip() == "" or str(x).strip() in NIET_GEVRAAGD


def _tekst(waarde) -> str:
    return "" if _leeg(waarde) else str(waarde).strip()


def _freq(waarde) -> int | None:
    if _leeg(waarde):
        return None
    w = str(waarde).strip().lower()
    if w.isdigit():
        return int(w)
    return next((code for stuk, code in FREQ_TEKST if stuk in w), None)


def _meerdere(opties: list[str], waarde) -> list[str]:
    """Meerkeuze in één cel, gescheiden door komma's. Per antwoord matchen, niet op de hele cel:
    anders telt een optie die het woord 'other' bevat ook als 'Other'. "Other, please specify" bevat zelf
    een komma en wordt eerst als één antwoord herkend."""
    if _leeg(waarde):
        return []
    w = re.sub(r"other,\s*please specify:?", "other", str(waarde), flags=re.IGNORECASE)
    gekozen = set()
    for antwoord in (a.strip() for a in w.split(",")):
        if not antwoord:
            continue
        doel = next((o for o in opties if o.lower() == antwoord.lower()), None)
        if doel is None:
            ONBEKENDE_OPTIES.add(antwoord)
        else:
            gekozen.add(doel)
    return [o for o in opties if o in gekozen]


def _schaal(waarde) -> int | None:
    if _leeg(waarde):
        return None
    w = str(waarde).strip().lower()
    if w in SCHAAL7:
        return SCHAAL7[w]
    getal = re.match(r"^\s*(\d+)", w)
    if getal and 1 <= int(getal.group(1)) <= 7:
        return int(getal.group(1))
    ONBEKENDE_LABELS.add(str(waarde).strip())
    return None


def _minuten(waarde) -> float | None:
    if _leeg(waarde):
        return None
    getal = re.search(r"\d+(?:[.,]\d+)?", str(waarde))
    return float(getal.group().replace(",", ".")) if getal else None


def _niveau(waarde) -> int | None:
    """Niveau 1-4 (index in NIVEAUS + 1)."""
    if _leeg(waarde):
        return None
    return next((i + 1 for i, n in enumerate(NIVEAUS) if n.lower() == str(waarde).strip().lower()), None)


def naar_records(df: pd.DataFrame, koppeling: dict) -> list[dict]:
    def cel(rij, veld):
        kolom = koppeling.get(veld)
        return rij.get(kolom) if kolom is not None else None

    records = []
    for i, rij in df.iterrows():
        freq = _freq(cel(rij, "freq"))
        gebruiker = freq is not None and freq <= GEBRUIKER_VANAF
        scores = {k: _schaal(cel(rij, k)) for k in ALLE_STELLINGEN}
        zorg = _schaal(cel(rij, "zorg"))
        h = houding(scores, zorg)
        afdeling = _tekst(cel(rij, "afdeling")) or "Unknown"
        records.append({
            "id": f"R{i + 1}",
            "afdeling": afdeling,
            "freq": freq,
            "freq_label": FREQ[freq - 1] if freq else "",
            "gebruiker": gebruiker,
            # vervolgvragen alleen voor gebruikers (routering): wat een niet-gebruiker toch invult telt niet
            "taken": _meerdere(TAKEN, cel(rij, "taken")) if gebruiker else [],
            "taken_anders": _tekst(cel(rij, "taken_anders")) if gebruiker else "",
            "niveau": _niveau(cel(rij, "niveau")) if gebruiker else None,
            "minuten_week": _minuten(cel(rij, "minuten")) if gebruiker else None,
            "scores": scores,
            "zorg": zorg,
            "gevoel": _meerdere(GEVOELENS, cel(rij, "gevoel")),
            "barrieres": _meerdere(BARRIERES, cel(rij, "barrieres")),
            "barrieres_anders": _tekst(cel(rij, "barrieres_anders")),
            "wat_helpt": _tekst(cel(rij, "wat_helpt")),
            "voorbeeld": _tekst(cel(rij, "voorbeeld")) if gebruiker else "",
            "houding": h,
            "persona": persona(freq, h),
        })
    return records


def filter_afgerond(df: pd.DataFrame, ook_onvolledig: bool = False) -> tuple[pd.DataFrame, str]:
    if ook_onvolledig or "Finished" not in df.columns:
        return df, f"{len(df)} respondents (no filter on completion)"
    klaar = df["Finished"].astype(str).str.lower().isin(["1", "true"])
    return df[klaar], f"{int(klaar.sum())} completed of {len(df)} started"
