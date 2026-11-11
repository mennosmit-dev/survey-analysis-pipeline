"""Kale PowerPoint met python-pptx: titelslide plus één grafiek per slide.

Bewust simpel: de titel is een plek voor de boodschap ("[Message] ..."), die schrijft een mens.
Opmaak in een huisstijl komt daarna, los van deze keten.
"""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Cm, Pt

INKT = RGBColor(0x0B, 0x0B, 0x0B)
GRIJS = RGBColor(0x52, 0x51, 0x4E)


def _tekst(slide, tekst, links, boven, breed, hoog, grootte, kleur=INKT, vet=False):
    vak = slide.shapes.add_textbox(Cm(links), Cm(boven), Cm(breed), Cm(hoog)).text_frame
    vak.word_wrap = True
    p = vak.paragraphs[0]
    p.text = tekst
    p.font.size, p.font.bold, p.font.color.rgb = Pt(grootte), vet, kleur


def maak(pad, titel, subtitel, dias: list[dict]):
    """dias: [{"titel": ..., "afbeelding": pad, "notitie": ...}]"""
    prs = Presentation()
    prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
    leeg = prs.slide_layouts[6]

    s = prs.slides.add_slide(leeg)
    _tekst(s, titel, 2, 6, 29, 3, 36, vet=True)
    _tekst(s, subtitel, 2, 9.5, 29, 2, 16, GRIJS)

    for d in dias:
        s = prs.slides.add_slide(leeg)
        _tekst(s, d["titel"], 1.5, 0.8, 30.5, 2.2, 22, vet=True)
        foto = s.shapes.add_picture(str(d["afbeelding"]), Cm(1.5), Cm(3.2), height=Cm(14.3))
        if foto.width > Cm(30.5):  # brede grafiek: op breedte schalen
            factor = Cm(30.5) / foto.width
            foto.width, foto.height = int(foto.width * factor), int(foto.height * factor)
        if d.get("notitie"):
            s.notes_slide.notes_text_frame.text = d["notitie"]
    # metadata neutraal: het lege python-pptx-sjabloon draagt anders de naam van de bibliotheekauteur mee
    prs.core_properties.author = prs.core_properties.last_modified_by = "survey-analysis-pipeline"
    prs.core_properties.title = titel
    prs.save(pad)
