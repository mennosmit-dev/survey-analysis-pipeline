"""Grafieken als PNG in neutrale kleuren: één boodschap per grafiek, n altijd in de voetnoot."""
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import KLEUR, PERSONA_KLEUR  # noqa: E402

plt.rcParams.update({"font.family": ["Segoe UI", "Arial", "DejaVu Sans", "sans-serif"], "font.size": 11,
                     "axes.edgecolor": KLEUR["lijn"], "text.color": KLEUR["tekst"],
                     "xtick.color": KLEUR["tekst2"], "ytick.color": KLEUR["tekst"],
                     "figure.facecolor": KLEUR["achtergrond"], "axes.facecolor": KLEUR["achtergrond"]})
REEKS_KLEUREN = [KLEUR["reeks1"], KLEUR["reeks2"], KLEUR["reeks3"]]


def _opmaak(ax, titel, voetnoot, fig):
    ax.set_title(titel, loc="left", fontsize=14, fontweight="bold", pad=14)
    for kant in ("top", "right", "bottom"):
        ax.spines[kant].set_visible(False)
    ax.xaxis.set_visible(False)
    regels = textwrap.wrap(voetnoot, 150)
    fig.text(0.01, 0.01, "\n".join(regels), fontsize=8.5, color=KLEUR["tekst2"], ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04 + 0.03 * (len(regels) - 1), 1, 1))


def staven(pad, titel, labels, reeksen: dict, voetnoot, procent=True):
    """Horizontale staven. `reeksen` = {naam: [waarden]}; None = niet getoond (bijv. groep te klein)."""
    hoogte = 0.8 / len(reeksen)
    fig, ax = plt.subplots(figsize=(10, max(3, 0.5 * len(labels) * max(1, len(reeksen) * 0.7) + 1.4)))
    for i, (naam, waarden) in enumerate(reeksen.items()):
        y = [j + i * hoogte for j in range(len(labels))]
        w = [0 if v is None else v * (100 if procent else 1) for v in waarden]
        balken = ax.barh(y, w, height=hoogte * 0.9, color=REEKS_KLEUREN[i % 3], label=naam)
        for b, v in zip(balken, waarden):
            tekst = "n<5" if v is None else (f"{v * 100:.0f}%" if procent else f"{v:.1f}")
            ax.text(b.get_width() + 0.5, b.get_y() + b.get_height() / 2, tekst, va="center", fontsize=9,
                    color=KLEUR["tekst2"])
    ax.set_yticks([j + hoogte * (len(reeksen) - 1) / 2 for j in range(len(labels))], labels)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)
    maximum = max([v * (100 if procent else 1) for w in reeksen.values() for v in w if v is not None] or [1])
    ax.set_xlim(0, maximum * 1.12)  # ruimte voor de waardelabels
    if len(reeksen) > 1:
        ax.legend(frameon=False, ncol=len(reeksen), loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=9)
    _opmaak(ax, titel, voetnoot, fig)
    fig.savefig(pad, dpi=110)
    plt.close(fig)


def persona_per_groep(pad, verdelingen: dict, voetnoot):
    """Gestapelde 100%-balk per groep, verdeeld over de persona's. `verdelingen` = {groep: {persona: aandeel}}."""
    fig, ax = plt.subplots(figsize=(10, 0.6 * len(verdelingen) + 1.8))
    for y, (groep, verdeling) in enumerate(verdelingen.items()):
        links = 0
        for p, kleur in PERSONA_KLEUR.items():
            w = (verdeling.get(p) or 0) * 100
            ax.barh(y, w, left=links, color=kleur, edgecolor=KLEUR["achtergrond"], linewidth=2,
                    label=p if y == 0 else None)
            if w >= 7:
                ax.text(links + w / 2, y, f"{w:.0f}%", ha="center", va="center", fontsize=9, color="white")
            links += w
    ax.set_yticks(range(len(verdelingen)), list(verdelingen))
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=9)
    _opmaak(ax, "Illustrative personas per department", voetnoot, fig)
    fig.savefig(pad, dpi=110)
    plt.close(fig)
