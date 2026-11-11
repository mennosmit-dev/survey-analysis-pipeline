"""Vergelijking met een referentiegroep. In dit voorbeeld is de referentiegroep SYNTHETISCH
(data/benchmark_synthetic.csv, gemaakt door make_synthetic_data.py).

Regel: vergelijk alleen vragen die echt overeenkomen. Bij een andere schaal vergelijken we alleen het
percentage dat het eens is (7-punts: 5-7; 5-punts: 4-5). Een ander vraagtype (ja/nee tegenover een
stelling) vergelijken we niet. Code 99999 betekent "niet gevraagd" en telt nergens mee.
"""
import pandas as pd

from config import DATA, EENS_VANAF_7, NIET_GEVRAAGD, WEKELIJKS_VANAF

PAD = DATA / "benchmark_synthetic.csv"

# label -> (functie op onze records, kolom in benchmark, functie op benchmarkwaarde)
VERGELIJKBAAR = {
    "Uses AI weekly or more": (lambda r: r["freq"] <= WEKELIJKS_VANAF if r["freq"] else None,
                               "freq_work", lambda w: w <= WEKELIJKS_VANAF),
    "Agrees: guidelines on AI use are clear": (
        lambda r: r["scores"]["s4"] >= EENS_VANAF_7 if r["scores"]["s4"] else None,
        "guidelines_clear_5pt", lambda w: w >= 4),  # 5-puntsschaal: 4-5 = eens
    "Agrees: worried about own job": (lambda r: r["zorg"] >= EENS_VANAF_7 if r["zorg"] else None,
                                      "worry_job_7pt", lambda w: w >= EENS_VANAF_7),
}
# Bewust NIET vergeleken (staat in de samenvatting, zodat niemand het later alsnog doet)
NIET_VERGELIJKBAAR = {"manager_support_yesno": "yes/no question in benchmark, 7-point statement (s3) in survey"}


def laad(pad=PAD) -> pd.DataFrame | None:
    if not pad.exists():
        return None
    df = pd.read_csv(pad, dtype=str)
    for k in df.columns[1:]:
        df[k] = pd.to_numeric(df[k].where(~df[k].isin(NIET_GEVRAAGD)), errors="coerce")
    return df


def vergelijk(records, bench: pd.DataFrame) -> pd.DataFrame:
    rijen = []
    for label, (eigen, kolom, regel) in VERGELIJKBAAR.items():
        w = [x for x in (eigen(r) for r in records) if x is not None]
        b = bench[kolom].dropna()
        rijen.append({"Measure": label, "Survey %": sum(w) / len(w) if w else None, "Survey n": len(w),
                      "Benchmark %": b.map(regel).mean() if len(b) else None, "Benchmark n": len(b)})
    return pd.DataFrame(rijen)
