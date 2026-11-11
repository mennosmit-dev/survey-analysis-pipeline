"""Maakt een SYNTHETISCHE enquête-export en een SYNTHETISCHE benchmark. Alle data is verzonnen.

    python make_synthetic_data.py            # 200 afgeronde + 10 onafgeronde respondenten, seed 42

Opbouw zoals een gangbare survey-tool-export (Qualtrics-stijl): rij 1 kolomcodes, rij 2 vraagtekst,
rij 3 ImportId's, daarna één rij per respondent. Meerkeuze staat in één cel, gescheiden door komma's.
Routering: vervolgvragen alleen voor wie AI maandelijks of vaker gebruikt. Een paar cellen krijgen -99
("gezien, niet beantwoord") zodat de keten die code moet afvangen.

Uitvoer: data/survey_export_synthetic.csv en data/benchmark_synthetic.csv
"""
import argparse
import csv
import json
import random

from config import AFDELINGEN, BARRIERES, DATA, FREQ, GEVOELENS, NEGATIEF, NIVEAUS, STELLINGEN, TAKEN, ZORG

SCHAAL = ["Strongly disagree", "Disagree", "Somewhat disagree", "Neutral", "Somewhat agree", "Agree",
          "Strongly agree"]
OPEN_HELP = ["More hands-on training", "Clear rules on what data I can use", "Examples from my own team",
             "Time set aside to experiment", "Access to a tool that works with our files", "", ""]
OPEN_VOORBEELD = ["Drafting a first version of a report", "Summarising long meeting notes",
                  "Writing formulas for a spreadsheet", "Translating a customer email", "Checking code for errors",
                  ""]

# Hoe vaak elke afdeling AI gebruikt: gewichten voor frequentiecode 1-6 (verzonnen, IT gebruikt het meest)
GEWICHTEN = {"IT": [4, 4, 3, 1, 1, 1], "Operations": [1, 2, 3, 2, 2, 3], "Finance": [1, 2, 3, 2, 2, 2],
             "HR": [1, 2, 2, 2, 2, 3], "Sales": [2, 3, 3, 2, 1, 2], "Legal": [1, 1, 2, 2, 2, 2]}
AFDELING_GEWICHT = [60, 40, 35, 30, 32]  # zonder Legal; die krijgt vast 3 respondenten (zie respondent())


def kolommen():
    k = [("StartDate", "Start Date"), ("Finished", "Finished"), ("ResponseId", "Response ID"),
         ("IPAddress", "IP Address"),
         ("Q1", "Which department do you work in?"),
         ("Q2", "How often do you use AI tools at work?"),
         ("Q3", "What do you use AI tools for? (select all that apply)"),
         ("Q3_7_TEXT", "What do you use AI tools for? (select all that apply) - Other - Text"),
         ("Q4", "Which description fits your most advanced use of AI?"),
         ("Q5", "About how many minutes per week does AI save you?")]
    k += [(f"Q6_{i + 1}", f"To what extent do you agree? - {tekst}")
          for i, tekst in enumerate(t for blok in STELLINGEN.values() for t in blok.values())]
    k += [("Q7", f"To what extent do you agree? - {ZORG[1]}"),
          ("Q8", "Which words describe how you feel about AI at work? (max. 3)"),
          ("Q9", "What are the biggest barriers to using AI in your work? (max. 3)"),
          ("Q9_8_TEXT", "What are the biggest barriers to using AI in your work? (max. 3) - Other - Text"),
          ("Q10", "What would help you use AI more in your work?"),
          ("Q11", "Describe one task where AI helped you recently.")]
    return k


def respondent(i: int, rnd: random.Random, afgerond: bool) -> dict:
    # Legal bewust kleiner dan MIN_GROEP: laat zien dat de keten die groep niet apart toont
    afd = "Legal" if i in (7, 77, 147) else rnd.choices(AFDELINGEN[:-1], weights=AFDELING_GEWICHT)[0]
    freq = rnd.choices(range(1, 7), weights=GEWICHTEN[afd])[0]
    gebruiker = freq <= 4
    # houding: vaker gebruik -> positiever (verzonnen verband, zodat de toetsen iets te vinden hebben)
    houding = rnd.gauss(0.9 - 0.35 * freq, 1.0)
    rij = {"StartDate": "2026-01-15 09:00:00", "Finished": "True" if afgerond else "False",
           "ResponseId": f"R_synthetic_{i:04d}", "IPAddress": f"192.0.2.{i % 250}",  # documentatiebereik
           "Q1": afd, "Q2": FREQ[freq - 1]}
    if gebruiker:
        taken = rnd.sample(TAKEN[:-1], k=rnd.randint(1, 3))
        if rnd.random() < 0.08:
            taken.append("Other")
            rij["Q3_7_TEXT"] = rnd.choice(["Meeting notes", "Planning shifts", "Writing job ads"])
        rij["Q3"] = ",".join(taken)
        max_niveau = 4 if freq <= 2 else 2
        rij["Q4"] = NIVEAUS[rnd.randint(0, max_niveau - 1)]
        rij["Q5"] = "-99" if rnd.random() < 0.04 else str(max(0, int(rnd.gauss(150 - 20 * freq, 60))))
        rij["Q11"] = rnd.choice(OPEN_VOORBEELD)
    for j in range(7):
        score = round(4 + houding + rnd.gauss(0, 1.1) + (0.6 if j == 2 else 0) - (0.8 if j == 3 else 0))
        rij[f"Q6_{j + 1}"] = SCHAAL[min(7, max(1, score)) - 1]
    rij["Q7"] = SCHAAL[min(7, max(1, round(4 - 0.6 * houding + rnd.gauss(0, 1.3)))) - 1]
    if rnd.random() < 0.03:
        rij["Q7"] = "-99"
    pos, neg = GEVOELENS[:4], sorted(NEGATIEF)
    aantal_neg = rnd.choices([0, 1, 2], weights=[max(0.2, 3 + 2 * houding), 2, max(0.1, 1 - 0.5 * houding)])[0]
    gevoel = rnd.sample(neg, aantal_neg) + rnd.sample(pos, rnd.randint(0 if aantal_neg else 1, 3 - aantal_neg))
    rij["Q8"] = ",".join(g for g in GEVOELENS if g in gevoel)
    bar = rnd.sample(BARRIERES[:-1], k=rnd.randint(1, 3))
    if rnd.random() < 0.05:
        bar.append("Other")
    rij["Q9"] = ",".join(bar)
    if "Other" in bar:
        rij["Q9_8_TEXT"] = rnd.choice(["Our laptops are too slow", "Not sure who to ask", "Language support"])
    rij["Q10"] = rnd.choice(OPEN_HELP)
    return rij


def schrijf_export(pad, n: int, n_onaf: int, seed: int):
    rnd = random.Random(seed)
    kol = kolommen()
    rijen = [respondent(i, rnd, afgerond=i < n) for i in range(n + n_onaf)]
    with open(pad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([c for c, _ in kol])
        w.writerow([t for _, t in kol])
        w.writerow([json.dumps({"ImportId": c}) for c, _ in kol])
        for r in rijen:
            w.writerow([r.get(c, "") for c, _ in kol])


def schrijf_benchmark(pad, n: int, seed: int):
    """Synthetische referentiegroep met een ANDERE opzet: codes in plaats van tekst, de stelling over
    richtlijnen op een 5-puntsschaal en code 99999 = niet gevraagd (een deel kreeg de vraag niet)."""
    rnd = random.Random(seed + 1)
    with open(pad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "freq_work", "guidelines_clear_5pt", "worry_job_7pt", "manager_support_yesno"])
        for i in range(n):
            freq = rnd.choices(range(1, 7), weights=[1, 2, 3, 2, 2, 3])[0]
            houding = rnd.gauss(0.6 - 0.3 * freq, 1.0)
            richtlijn = 99999 if rnd.random() < 0.2 else min(5, max(1, round(3 + 0.6 * houding + rnd.gauss(0, 1))))
            zorg = min(7, max(1, round(4.3 - 0.5 * houding + rnd.gauss(0, 1.3))))
            w.writerow([f"B{i:04d}", freq, richtlijn, zorg, rnd.choice([0, 1])])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=200, help="aantal afgeronde respondenten")
    p.add_argument("--onafgerond", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    DATA.mkdir(exist_ok=True)
    schrijf_export(DATA / "survey_export_synthetic.csv", args.n, args.onafgerond, args.seed)
    schrijf_benchmark(DATA / "benchmark_synthetic.csv", 600, args.seed)
    print(f"Synthetische data geschreven naar {DATA} ({args.n} afgerond + {args.onafgerond} onafgerond, "
          f"seed {args.seed}; benchmark n=600)")


if __name__ == "__main__":
    main()
