"""Eén commando voor de hele analyse.

    python run_pipeline.py                       # nieuwste export in data/
    python run_pipeline.py data/export.csv       # specifieke export
    python run_pipeline.py --include-incomplete  # ook niet-afgeronde respondenten

Schrijft naar output/: tables.xlsx, charts/*.png, deck.pptx, summary.md, open_answers.md en mapping.md.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

import analysis
import benchmark
import charts
import read_export
import slides
from config import AFDELINGEN, DATA, FREQ, MIN_GROEP, ORGANISATIE, OUTPUT, PERSONAS


def pct(x):
    return "" if x is None or pd.isna(x) else f"{x * 100:.0f}%"


def pwaarde(df):
    """p-waarden leesbaar: '<0.001' in plaats van een afgeronde 0."""
    df = df.copy()
    for k in [c for c in df.columns if c in ("p", "p (BH)")]:
        df[k] = df[k].map(lambda v: "" if v is None or pd.isna(v) else ("<0.001" if v < 0.001 else f"{v:.3f}"))
    return df


def kies_export(arg):
    if arg:
        return arg
    exports = sorted([f for f in DATA.glob("*") if f.suffix.lower() in (".csv", ".xlsx")
                      and not f.name.startswith("benchmark")], key=lambda f: f.stat().st_mtime)
    if not exports:
        sys.exit("No export found. Run `python make_synthetic_data.py` or put an export (CSV/XLSX) in data/.")
    return exports[-1]


def main(argv=None, uitvoer=OUTPUT):
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("export", nargs="?")
    p.add_argument("--include-incomplete", action="store_true")
    args = p.parse_args(argv)
    bron = kies_export(args.export)
    grafiek = uitvoer / "charts"
    grafiek.mkdir(parents=True, exist_ok=True)

    # 1. Inlezen en koppelen
    df, teksten = read_export.lees_export(bron)
    df, filtertekst = read_export.filter_afgerond(df, args.include_incomplete)
    koppeling, waarschuwingen = read_export.koppel_kolommen(teksten)
    records = read_export.naar_records(df, koppeling)
    waarschuwingen += [f"Unknown scale label '{l}' ignored; add it to SCHAAL7 in config.py"
                       for l in sorted(read_export.ONBEKENDE_LABELS)]
    waarschuwingen += [f"Unknown multiple-choice option '{o}' ignored; add it to config.py"
                       for o in sorted(read_export.ONBEKENDE_OPTIES)]
    (uitvoer / "mapping.md").write_text(
        "# Field -> column mapping\n\n| Field | Column | Question text |\n| --- | --- | --- |\n"
        + "\n".join(f"| {v} | {k} | {teksten.get(k, '')[:110]} |" for v, k in koppeling.items())
        + "\n\n## Warnings\n\n" + ("\n".join(f"- {w}" for w in waarschuwingen) or "None") + "\n",
        encoding="utf-8")

    # 2. Tabellen, toetsen en vergelijking
    n = len(records)
    geb = analysis.gebruikers(records)
    tabellen = analysis.alle_tabellen(records)
    toetsen = analysis.toetsen(records)
    kc = analysis.kerncijfers(records)
    per_afd, weggelaten = analysis.per_groep(records, "afdeling", AFDELINGEN)
    bench = benchmark.laad()
    vergelijking = benchmark.vergelijk(records, bench) if bench is not None else None

    with pd.ExcelWriter(uitvoer / "tables.xlsx") as x:
        pd.Series(kc, name="Value").to_excel(x, sheet_name="Key figures")
        per_afd.to_excel(x, sheet_name="Per department")
        for naam, t in {**tabellen, **toetsen}.items():
            t.to_excel(x, sheet_name=naam[:31], index=naam.startswith("Crosstab"))
        if vergelijking is not None:
            vergelijking.to_excel(x, sheet_name="Benchmark (synthetic)", index=False)

    # 3. Grafieken en slides
    voet = f"Synthetic data. n={n}"
    voet_geb = f"Synthetic data. Users only (monthly or more): n={len(geb)}"
    dias = []

    def dia(bestand, titel, notitie=""):
        dias.append({"titel": titel, "afbeelding": grafiek / bestand, "notitie": notitie})

    charts.staven(grafiek / "01_use_at_work.png", "How often do you use AI tools at work?", FREQ,
                  {"All respondents": tabellen["Use at work"]["Share"].tolist()}, voet)
    dia("01_use_at_work.png", "[Message] Use of AI at work",
        f"Weekly or more: {pct(kc['Uses AI weekly or more'])}")

    t = tabellen["Tasks (users)"]
    charts.staven(grafiek / "02_tasks.png", "What do you use AI tools for?", t["Answer"].tolist(),
                  {"Users": t["Share"].tolist()}, voet_geb + ". Multiple answers possible.")
    dia("02_tasks.png", "[Message] What people use AI for")

    t = tabellen["Level x minutes"]
    charts.staven(grafiek / "03_minutes_by_level.png", "Minutes saved per week, by most advanced use",
                  [f"{d} (n={k})" for d, k in zip(t["Description"], t["n"])],
                  {"Users": t["Mean minutes/week"].tolist()},
                  voet_geb + f". Mean minutes; groups under {MIN_GROEP} not shown.", procent=False)
    dia("03_minutes_by_level.png", "[Message] Time saved grows with depth of use")

    t = tabellen["Statements"]
    mw = toetsen["Mann-Whitney"].set_index("Item")
    labels = [f"{s}{' *' if mw.loc[k, 'Significant (BH < .05)'] else ''}" for k, s in zip(t["Item"], t["Statement"])]
    weekly = [r for r in records if (r["freq"] or 9) <= 3]
    rest = [r for r in records if (r["freq"] or 9) > 3]
    charts.staven(grafiek / "04_statements_by_use.png", "Statements: % agree (5-7), weekly users vs. the rest",
                  labels, {f"Weekly or more (n={len(weekly)})": [analysis.pct_eens([r['scores'][k] for r in weekly])
                                                                for k in t["Item"]],
                           f"Less often (n={len(rest)})": [analysis.pct_eens([r['scores'][k] for r in rest])
                                                          for k in t["Item"]]},
                  voet + ". * = Mann-Whitney U, Benjamini-Hochberg corrected p < .05.")
    dia("04_statements_by_use.png", "[Message] Weekly users see more value and support")

    t = tabellen["Barriers"]
    charts.staven(grafiek / "05_barriers.png", "Biggest barriers to using AI (max. 3)", t["Answer"].tolist(),
                  {"All respondents": t["Share"].tolist()}, voet)
    dia("05_barriers.png", "[Message] What holds people back")

    verdelingen = {}
    for afd in AFDELINGEN:
        sub = [r for r in records if r["afdeling"] == afd and r["persona"]]
        if len(sub) >= MIN_GROEP:
            verdelingen[f"{afd} (n={len(sub)})"] = {p: analysis.aandeel(sub, lambda r, p=p: r["persona"] == p)
                                                    for p in PERSONAS}
    alle = [r for r in records if r["persona"]]
    verdelingen[f"All (n={len(alle)})"] = {p: analysis.aandeel(alle, lambda r, p=p: r["persona"] == p)
                                           for p in PERSONAS}
    chi = toetsen["Chi-square"].iloc[0]
    charts.persona_per_groep(grafiek / "06_personas.png", verdelingen,
                             voet + f". Illustrative rules (see personas.py). Departments under {MIN_GROEP} "
                             f"left out: {', '.join(weggelaten) or 'none'}.")
    dia("06_personas.png", "[Message] Personas per department",
        f"Department x weekly use: chi2={chi['chi2']:.1f}, df={chi['df']}, p={chi['p']:.3f}, "
        f"Cramer's V={chi['cramers_v']:.2f}")

    if vergelijking is not None:
        charts.staven(grafiek / "07_benchmark.png", "Survey vs. synthetic benchmark (matching questions only)",
                      vergelijking["Measure"].tolist(),
                      {f"Survey (n={n})": vergelijking["Survey %"].tolist(),
                       "Benchmark, synthetic": vergelijking["Benchmark %"].tolist()},
                      voet + ". Benchmark is synthetic too. Different scales compared as % agree only "
                      "(7-point: 5-7, 5-point: 4-5); code 99999 = not asked, excluded.")
        dia("07_benchmark.png", "[Message] How we compare")

    slides.maak(uitvoer / "deck.pptx", f"AI adoption survey: {ORGANISATIE}",
                f"Synthetic data, n={n} · {date.today():%Y-%m-%d}", dias)

    # 4. Open antwoorden en samenvatting
    (uitvoer / "open_answers.md").write_text(analysis.open_antwoorden_md(records), encoding="utf-8")
    fmt = lambda v: v if isinstance(v, str) else ("" if v is None or pd.isna(v) else
                                                  (f"{v:.0f}" if abs(v) > 1 else pct(v)))
    regels = [f"# Summary: AI adoption survey ({ORGANISATIE}, synthetic data)", "",
              f"- Source: `{Path(bron).name}`", f"- Respondents: {filtertekst}",
              f"- Mapping: {len(koppeling)} fields, {len(waarschuwingen)} warnings (see mapping.md)",
              f"- Departments not shown (n<{MIN_GROEP}): {', '.join(weggelaten) or 'none'}", "",
              "## Key figures", "", pd.Series(kc).map(fmt).to_frame("Value").to_markdown(), "",
              "## Themes (mean 1-7)", "", tabellen["Themes"].round(2).to_markdown(index=False), "",
              "## Statements", "", tabellen["Statements"].round(2).to_markdown(index=False), "",
              "## Significance tests", "", pwaarde(toetsen["Chi-square"].round(3)).to_markdown(index=False), "",
              pwaarde(toetsen["Mann-Whitney"][["Item", "Mean weekly+", "Mean less often", "n1", "n2", "U", "p",
                                               "p (BH)", "r"]].round(3)).to_markdown(index=False), "",
              "## Per department", "",
              per_afd.map(lambda v: f"{v:.2f}" if isinstance(v, float) else v).to_markdown(), "",
              "## Persona profile (illustrative rules)", "",
              tabellen["Persona profile"].round(2).to_markdown(index=False), ""]
    if vergelijking is not None:
        regels += ["## Benchmark (synthetic, matching questions only)", "",
                   vergelijking.round(3).to_markdown(index=False), "",
                   "Not compared: " + "; ".join(f"{k} ({v})" for k, v in benchmark.NIET_VERGELIJKBAAR.items())]
    (uitvoer / "summary.md").write_text("\n".join(regels) + "\n", encoding="utf-8")

    print(f"Done. {filtertekst}. Output in {uitvoer.name}/")
    for w in waarschuwingen:
        print(" ! " + w)
    return records


if __name__ == "__main__":
    main()
