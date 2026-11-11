"""Vaste definities voor de enquête-analyse: antwoordopties, stellingen, persona-regels, kleuren en paden.

Alles hier hoort bij een VERZONNEN enquête ("AI-gebruik op het werk") bij een fictieve organisatie.
Pas dit bestand aan voor een andere vragenlijst; de rest van de keten leest alleen deze definities.
"""
from pathlib import Path

HIER = Path(__file__).parent
DATA = HIER / "data"
OUTPUT = HIER / "output"

ORGANISATIE = "Example Org (fictional)"

MIN_GROEP = 5  # groepen kleiner dan dit niet apart tonen (anonimiteit)

# Codes in een export die "niet gevraagd" of "gezien maar niet beantwoord" betekenen. Tellen nergens mee.
NIET_GEVRAAGD = {"-99", "-99.0", "99999", "99999.0"}

AFDELINGEN = ["Operations", "Finance", "IT", "HR", "Sales", "Legal"]

# Frequentie: code 1-6, laag = vaak
FREQ = ["Several times a day", "Daily", "Weekly", "Monthly", "A few times a year", "Never"]
GEBRUIKER_VANAF = 4  # t/m maandelijks krijgt de vervolgvragen (routering)
WEKELIJKS_VANAF = 3

TAKEN = ["Writing and editing", "Summarising documents", "Searching for information", "Data analysis",
         "Coding", "Brainstorming", "Other"]

NIVEAUS = ["Occasional prompts", "Part of my weekly routine", "Automating steps of a task",
           "Building tools for colleagues"]

GEVOELENS = ["Curious", "Optimistic", "Confident", "Relaxed", "Uncertain", "Sceptical", "Overwhelmed", "Worried"]
NEGATIEF = {"Uncertain", "Sceptical", "Overwhelmed", "Worried"}

BARRIERES = ["Lack of time", "Lack of training", "Unclear rules", "Data privacy concerns",
             "Output is not reliable", "Not relevant for my work", "No access to tools", "Other"]

# Stellingen op een 7-puntsschaal, gegroepeerd in drie thema's
STELLINGEN = {
    "Skills": {"s1": "I know how to use AI tools safely",
               "s2": "I can judge whether AI output is correct"},
    "Support": {"s3": "My manager encourages me to try AI tools",
                "s4": "Our guidelines on AI use are clear",
                "s5": "I have enough time to learn new tools"},
    "Value": {"s6": "AI improves the quality of my work",
              "s7": "AI saves me time on routine work"},
}
ALLE_STELLINGEN = {k: v for blok in STELLINGEN.values() for k, v in blok.items()}
ZORG = ("worry", "I worry that AI will change my job in ways I do not want")

SCHAAL7 = {"strongly disagree": 1, "disagree": 2, "somewhat disagree": 3, "neutral": 4,
           "somewhat agree": 5, "agree": 6, "strongly agree": 7}
EENS_VANAF_7 = 5  # 5-7 telt als "eens"

# Illustratieve persona's (eigen regels, zie personas.py). Volgorde = volgorde in grafieken.
PERSONAS = ["Champion", "Pragmatist", "Curious starter", "Sceptic"]

# Neutrale kleuren (referentiepalet uit een generieke dataviz-richtlijn), geen huisstijl
KLEUR = {"reeks1": "#2a78d6", "reeks2": "#eb6834", "reeks3": "#1baf7a", "reeks4": "#eda100",
         "tekst": "#0b0b0b", "tekst2": "#52514e", "lijn": "#d6d5d0", "achtergrond": "#fcfcfb"}
PERSONA_KLEUR = dict(zip(PERSONAS, [KLEUR["reeks1"], KLEUR["reeks3"], KLEUR["reeks4"], KLEUR["reeks2"]]))
