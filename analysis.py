"""Analyses op de records: kerncijfers, tabellen per vraag, stellingen, kruisingen, toetsen en persona's."""
from collections import Counter

import pandas as pd

import stats_tests
from config import (AFDELINGEN, BARRIERES, EENS_VANAF_7, FREQ, GEVOELENS, MIN_GROEP, NEGATIEF, NIVEAUS, PERSONAS,
                    STELLINGEN, TAKEN, WEKELIJKS_VANAF)


def gebruikers(records):
    return [r for r in records if r["gebruiker"]]


def aandeel(lijst, voorwaarde):
    return sum(1 for x in lijst if voorwaarde(x)) / len(lijst) if lijst else None


def pct_eens(waarden):
    w = [x for x in waarden if x is not None]
    return sum(1 for x in w if x >= EENS_VANAF_7) / len(w) if w else None


def kerncijfers(records) -> dict:
    geb = gebruikers(records)
    minuten = pd.Series([r["minuten_week"] for r in geb if r["minuten_week"] is not None], dtype=float)
    met_persona = [r for r in records if r["persona"]]
    uit = {
        "n": len(records),
        "Uses AI at work (monthly or more)": aandeel(records, lambda r: r["gebruiker"]),
        "Uses AI weekly or more": aandeel(records, lambda r: (r["freq"] or 9) <= WEKELIJKS_VANAF),
        "Uses AI daily or more": aandeel(records, lambda r: (r["freq"] or 9) <= 2),
        "Mean minutes saved per week (users)": minuten.mean() if len(minuten) else None,
        "Median minutes saved per week (users)": minuten.median() if len(minuten) else None,
        "Only positive feelings": aandeel(records, lambda r: bool(r["gevoel"])
                                          and not any(g in NEGATIEF for g in r["gevoel"])),
        "Agrees: worried about own job": pct_eens([r["zorg"] for r in records]),
    }
    for p in PERSONAS:
        uit[f"Persona: {p}"] = aandeel(met_persona, lambda r, p=p: r["persona"] == p)
    return uit


def telling(records, veld, opties, basis=None) -> pd.DataFrame:
    """Aantal en aandeel per antwoordoptie. `basis` = de records die de vraag kregen (routering);
    de kolom Base laat die n altijd zien."""
    basis = records if basis is None else basis
    c = Counter()
    for r in basis:
        waarde = r[veld]
        for w in (waarde if isinstance(waarde, list) else [waarde]):
            c[w] += 1
    rijen = [(o, c.get(o, 0), c.get(o, 0) / len(basis) if basis else None) for o in opties]
    return pd.DataFrame(rijen, columns=["Answer", "Count", "Share"]).assign(Base=len(basis))


def stellingen(records) -> pd.DataFrame:
    uit = []
    for blok, items in STELLINGEN.items():
        for k, tekst in items.items():
            w = pd.Series([r["scores"][k] for r in records if r["scores"][k] is not None], dtype=float)
            uit.append({"Theme": blok, "Item": k, "Statement": tekst, "n": len(w),
                        "Mean (1-7)": w.mean() if len(w) else None,
                        "% agree (5-7)": (w >= EENS_VANAF_7).mean() if len(w) else None})
    return pd.DataFrame(uit)


def themas(records) -> pd.DataFrame:
    return stellingen(records).groupby("Theme", sort=False)["Mean (1-7)"].mean().reset_index()


def per_groep(records, veld, groepen) -> tuple[pd.DataFrame, list[str]]:
    """Kerncijfers per groep; groepen kleiner dan MIN_GROEP worden niet getoond (anonimiteit)."""
    kolommen, weggelaten = {}, []
    for g in groepen:
        sub = [r for r in records if r[veld] == g]
        if len(sub) < MIN_GROEP:
            weggelaten.append(f"{g} (n={len(sub)})")
            continue
        kc = kerncijfers(sub)
        kc.update({f"Theme: {t}": v for t, v in themas(sub).itertuples(index=False)})
        kolommen[g] = kc
    return pd.DataFrame(kolommen), weggelaten


def kruistabel(records, rij_veld, rij_opties, kolom_veld, kolom_opties) -> tuple[pd.DataFrame, list[str]]:
    """Aantallen rij x kolom. Rijen onder MIN_GROEP gaan eruit (en worden gemeld)."""
    tabel, weggelaten = {}, []
    for ro in rij_opties:
        sub = [r for r in records if r[rij_veld] == ro]
        if len(sub) < MIN_GROEP:
            weggelaten.append(f"{ro} (n={len(sub)})")
            continue
        tabel[ro] = [sum(1 for r in sub if r[kolom_veld] == ko) for ko in kolom_opties]
    return pd.DataFrame.from_dict(tabel, orient="index", columns=kolom_opties), weggelaten


def toetsen(records) -> dict[str, pd.DataFrame]:
    """1) chi-kwadraat: afdeling x wekelijks gebruik; 2) Mann-Whitney per stelling: gebruikers (wekelijks+)
    tegenover de rest, met Benjamini-Hochberg-correctie over alle stellingen."""
    for r in records:
        r["_wekelijks"] = "Weekly or more" if (r["freq"] or 9) <= WEKELIJKS_VANAF else "Less often"
    kt, weggelaten = kruistabel(records, "afdeling", AFDELINGEN, "_wekelijks", ["Weekly or more", "Less often"])
    chi = stats_tests.chi2_onafhankelijkheid(kt.values)
    chi_df = pd.DataFrame([{"Test": "Department x weekly use (chi-square)", **chi,
                            "Left out (n<%d)" % MIN_GROEP: ", ".join(weggelaten) or "none"}]).rename(
        columns={"aandeel_verwacht_onder_5": "share_expected_below_5"})

    rijen = []
    items = [(k, t) for blok in STELLINGEN.values() for k, t in blok.items()]
    for k, tekst in items:
        a = [r["scores"][k] for r in records if r["_wekelijks"] == "Weekly or more" and r["scores"][k] is not None]
        b = [r["scores"][k] for r in records if r["_wekelijks"] == "Less often" and r["scores"][k] is not None]
        mw = stats_tests.mann_whitney(a, b)
        rijen.append({"Item": k, "Statement": tekst, "Mean weekly+": sum(a) / len(a) if a else None,
                      "Mean less often": sum(b) / len(b) if b else None, **mw})
    mw_df = pd.DataFrame(rijen)
    mw_df["p (BH)"] = stats_tests.benjamini_hochberg(mw_df["p"].tolist())
    mw_df["Significant (BH < .05)"] = mw_df["p (BH)"] < 0.05
    kt_pct = kt.div(kt.sum(axis=1), axis=0)
    return {"Crosstab dept x use": kt.assign(n=kt.sum(axis=1)), "Crosstab dept x use %": kt_pct,
            "Chi-square": chi_df, "Mann-Whitney": mw_df}


def niveau_minuten(records) -> pd.DataFrame:
    rijen = []
    for d in range(1, 5):
        m = [r["minuten_week"] for r in records if r["niveau"] == d and r["minuten_week"] is not None]
        rijen.append({"Level": d, "Description": NIVEAUS[d - 1], "n": len(m),
                      "Mean minutes/week": sum(m) / len(m) if len(m) >= MIN_GROEP else None})
    return pd.DataFrame(rijen)


def persona_profiel(records) -> pd.DataFrame:
    rijen = []
    for p in PERSONAS:
        sub = [r for r in records if r["persona"] == p]
        rij = {"Persona": p, "n": len(sub)}
        if len(sub) >= MIN_GROEP:
            rij.update({t: v for t, v in themas(sub).itertuples(index=False)})
            top = Counter(b for r in sub for b in r["barrieres"]).most_common(3)
            rij["Top barriers"] = "; ".join(f"{b} ({n})" for b, n in top)
        rijen.append(rij)
    return pd.DataFrame(rijen)


def open_antwoorden_md(records) -> str:
    vragen = {"wat_helpt": "What would help you use AI more in your work?",
              "voorbeeld": "Describe one task where AI helped you recently. (users only)",
              "taken_anders": "Other uses (Other - text)", "barrieres_anders": "Other barriers (Other - text)"}
    delen = ["# Open answers\n", "Raw answers without department, to limit recognisability.\n"]
    for veld, vraag in vragen.items():
        antwoorden = [r[veld] for r in records if r[veld]]
        delen.append(f"\n## {vraag}\n\n{len(antwoorden)} answers\n")
        delen += [f"- {a}" for a in antwoorden]
    return "\n".join(delen) + "\n"


def alle_tabellen(records) -> dict[str, pd.DataFrame]:
    geb = gebruikers(records)
    return {
        "Department": telling(records, "afdeling", AFDELINGEN),
        "Use at work": telling(records, "freq_label", FREQ),
        "Tasks (users)": telling(geb, "taken", TAKEN).sort_values("Count", ascending=False),
        "Level (users)": telling(geb, "niveau", [1, 2, 3, 4]).assign(Answer=lambda d: NIVEAUS),
        "Feelings": telling(records, "gevoel", GEVOELENS).sort_values("Count", ascending=False),
        "Barriers": telling(records, "barrieres", BARRIERES).sort_values("Count", ascending=False),
        "Personas": telling([r for r in records if r["persona"]], "persona", PERSONAS),
        "Statements": stellingen(records),
        "Themes": themas(records),
        "Level x minutes": niveau_minuten(records),
        "Persona profile": persona_profiel(records),
    }
