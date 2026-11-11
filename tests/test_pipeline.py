"""Tests voor de logica die stil fout kan gaan. Draaien met: python -m pytest -q"""
import hashlib

import pandas as pd
import pytest
from pptx import Presentation

import analysis
import benchmark
import make_synthetic_data
import read_export
import run_pipeline
import stats_tests
from personas import houding, persona


# --- Statistiek: vergeleken met bekende tabelwaarden ---

@pytest.mark.parametrize("x, df, verwacht", [(3.841459, 1, 0.05), (5.991465, 2, 0.05), (11.0705, 5, 0.05),
                                             (6.634897, 1, 0.01), (0.454936, 1, 0.5), (30.0, 3, 1.38e-6)])
def test_chi2_overschrijdingskans(x, df, verwacht):
    assert stats_tests.chi2_sf(x, df) == pytest.approx(verwacht, rel=1e-3)


def test_chi2_kruistabel_met_de_hand_gerekend():
    # verwacht 12/18/28/42 -> chi2 = 4/12 + 4/18 + 4/28 + 4/42 = 0.7937
    uit = stats_tests.chi2_onafhankelijkheid([[10, 20], [30, 40]])
    assert uit["chi2"] == pytest.approx(0.7937, abs=1e-4)
    assert uit["df"] == 1
    assert uit["p"] == pytest.approx(0.3730, abs=1e-3)
    assert uit["aandeel_verwacht_onder_5"] == 0


def test_mann_whitney_volledig_gescheiden():
    # U = 0; mu = 12.5; sigma = sqrt(25 * 11 / 12); z = -12 / sigma = -2.507; p = 0.0122
    uit = stats_tests.mann_whitney([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
    assert uit["U"] == 0
    assert uit["z"] == pytest.approx(-2.5067, abs=1e-3)
    assert uit["p"] == pytest.approx(0.0122, abs=1e-3)
    assert uit["r"] == -1


def test_mann_whitney_gelijke_groepen_en_knopen():
    uit = stats_tests.mann_whitney([3, 4, 4, 5], [3, 4, 4, 5])
    assert uit["p"] == pytest.approx(1.0)
    assert stats_tests.mann_whitney([4, 4], [4, 4])["p"] == 1.0  # alles gelijk: geen deling door nul


def test_benjamini_hochberg():
    uit = stats_tests.benjamini_hochberg([0.01, 0.04, 0.03, 0.2, None])
    assert uit[:4] == pytest.approx([0.04, 0.05333, 0.05333, 0.2], abs=1e-4)
    assert uit[4] is None


# --- Persona's (illustratieve eigen regels) ---

@pytest.mark.parametrize("freq, h, verwacht", [
    (1, 5.0, "Champion"), (3, 6.5, "Champion"), (3, 4.9, "Pragmatist"),
    (4, 4.0, "Curious starter"),  # maandelijks is niet wekelijks
    (6, 3.9, "Sceptic"), (None, 5.0, None), (2, None, None)])
def test_persona(freq, h, verwacht):
    assert persona(freq, h) == verwacht


def test_houding_gebruikt_value_en_zorg():
    assert houding({"s6": 6, "s7": 4}, None) == 5
    assert houding({"s6": 6, "s7": 4}, 6) == 4  # zorg 6 trekt 1 punt af
    assert houding({"s6": None, "s7": None}, 2) is None


# --- Inlezen ---

def test_frequentie_tekst_en_code():
    assert read_export._freq("Several times a day") == 1
    assert read_export._freq("A few times a year") == 5
    assert read_export._freq("3") == 3
    assert read_export._freq("-99") is None  # gezien, niet beantwoord


def test_meerkeuze_met_komma_in_other():
    read_export.ONBEKENDE_OPTIES.clear()
    uit = read_export._meerdere(["Lack of time", "Unclear rules", "Other"], "Unclear rules,Other, please specify:,Lack of time")
    assert uit == ["Lack of time", "Unclear rules", "Other"]
    read_export._meerdere(["Lack of time"], "Lack of time,Budget")
    assert read_export.ONBEKENDE_OPTIES == {"Budget"}


def test_schaal_labels_getallen_en_codes():
    assert read_export._schaal("Strongly agree") == 7
    assert read_export._schaal("Somewhat disagree") == 3
    assert read_export._schaal("5") == 5
    assert read_export._schaal("99999") is None
    assert read_export._schaal("Don't know") is None
    assert "Don't know" in read_export.ONBEKENDE_LABELS


def test_privacykolommen_weg_en_dubbele_codes(tmp_path):
    pad = tmp_path / "export.csv"
    pad.write_text("IPAddress,Q1,Q2,Q2\nIP Address,Which department do you work in?,A,B\n192.0.2.1,IT,x,y\n",
                   encoding="utf-8")
    df, teksten = read_export.lees_export(pad)
    assert list(df.columns) == ["Q1", "Q2", "Q2.1"]
    assert "IPAddress" not in teksten


def test_in_excel_opgeslagen_export_wordt_geweigerd(tmp_path):
    pad = tmp_path / "export.csv"
    pad.write_text('StartDate,IPAddress,Q1\n"Start Date,IP Address,""Department"""\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="Excel"):
        read_export.lees_export(pad)


def test_routering_niet_gebruiker_krijgt_geen_vervolgvragen():
    df = pd.DataFrame([{"F": "Never", "T": "Coding", "M": "60"}, {"F": "Weekly", "T": "Coding", "M": "60"}])
    r = read_export.naar_records(df, {"freq": "F", "taken": "T", "minuten": "M"})
    assert r[0]["taken"] == [] and r[0]["minuten_week"] is None
    assert r[1]["taken"] == ["Coding"] and r[1]["minuten_week"] == 60


# --- Analyse: anonimiteit en vergelijkbaarheid ---

def _rec(afdeling="IT", freq=2, s=5, zorg=3):
    scores = {k: s for k in ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]}
    return {"afdeling": afdeling, "freq": freq, "gebruiker": freq <= 4, "minuten_week": 60, "scores": scores,
            "zorg": zorg, "gevoel": ["Curious"], "barrieres": [], "niveau": 1, "taken": [],
            "persona": persona(freq, houding(scores, zorg))}


def test_kleine_groep_wordt_niet_getoond():
    records = [_rec("IT")] * 5 + [_rec("Legal")] * 4
    tabel, weggelaten = analysis.per_groep(records, "afdeling", ["IT", "Legal"])
    assert list(tabel.columns) == ["IT"]
    assert weggelaten == ["Legal (n=4)"]
    kt, weg = analysis.kruistabel(records, "afdeling", ["IT", "Legal"], "freq", [2])
    assert list(kt.index) == ["IT"] and weg == ["Legal (n=4)"]


def test_benchmark_alleen_vergelijkbaar_en_99999_telt_niet(tmp_path):
    pad = tmp_path / "b.csv"
    pad.write_text("id,freq_work,guidelines_clear_5pt,worry_job_7pt,manager_support_yesno\n"
                   "B1,1,5,7,1\nB2,6,2,1,0\nB3,2,99999,4,1\n", encoding="utf-8")
    b = benchmark.laad(pad)
    uit = benchmark.vergelijk([_rec(s=5), _rec(s=3)], b).set_index("Measure")
    assert uit.loc["Agrees: guidelines on AI use are clear", "Benchmark n"] == 2  # 99999 eruit
    assert uit.loc["Agrees: guidelines on AI use are clear", "Benchmark %"] == 0.5  # 5-punts: 4-5 = eens
    assert uit.loc["Agrees: guidelines on AI use are clear", "Survey %"] == 0.5  # 7-punts: 5-7 = eens
    assert "manager_support_yesno" not in set(uit.index)


# --- Van begin tot eind op de synthetische data ---

@pytest.fixture(scope="module")
def synthetisch(tmp_path_factory):
    map_ = tmp_path_factory.mktemp("data")
    make_synthetic_data.schrijf_export(map_ / "export.csv", 200, 10, 42)
    return map_ / "export.csv"


def test_synthetische_data_is_reproduceerbaar(synthetisch, tmp_path):
    make_synthetic_data.schrijf_export(tmp_path / "opnieuw.csv", 200, 10, 42)
    hash_ = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert hash_(synthetisch) == hash_(tmp_path / "opnieuw.csv")


def test_synthetische_export_koppelt_volledig(synthetisch):
    df, teksten = read_export.lees_export(synthetisch)
    df, _ = read_export.filter_afgerond(df)
    koppeling, waarschuwingen = read_export.koppel_kolommen(teksten)
    records = read_export.naar_records(df, koppeling)
    assert waarschuwingen == []
    assert len(records) == 200
    assert all(r["niveau"] is None for r in records if not r["gebruiker"])
    assert any(r["minuten_week"] is None for r in records if r["gebruiker"])  # -99 is afgevangen
    _, weggelaten = analysis.per_groep(records, "afdeling", ["Legal"])
    assert weggelaten == ["Legal (n=3)"]


def test_pipeline_van_begin_tot_eind(synthetisch, tmp_path):
    run_pipeline.main([str(synthetisch)], uitvoer=tmp_path)
    for bestand in ["tables.xlsx", "deck.pptx", "summary.md", "open_answers.md", "mapping.md"]:
        assert (tmp_path / bestand).exists(), bestand
    assert len(list((tmp_path / "charts").glob("*.png"))) >= 6
    dias = len(Presentation(tmp_path / "deck.pptx").slides)
    assert dias == 1 + len(list((tmp_path / "charts").glob("*.png")))  # titel + één grafiek per slide
    assert "Legal (n=3)" in (tmp_path / "summary.md").read_text(encoding="utf-8")
