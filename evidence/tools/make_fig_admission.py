"""Fig: run-time admission by stratum. Data = Table 'Run-time admission' of the manuscript (counts from the run-time measurement, two full passes)."""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
G = [("Class", [("Knife", 3457, 2615), ("Gun", 5371, 3576), ("Stick", 506, 243)]),
     ("Image shape", [("Square", 1743, 1743), ("Wide", 6661, 4384), ("Tall", 930, 307)]),
     ("Source", [("D3", 2134, 1894), ("D2", 5470, 3839), ("D4", 1564, 695), ("Other", 166, 6)]),
     ("Object size", [("Small", 222, 201), ("Medium", 2037, 1580), ("Large", 7075, 4653)])]
OVERALL = 6434 / 9334
INK, MUTED, BAR, GRID = "#1a1a1a", "#555555", "#3b5b7a", "#d0d0d0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(119 / 25.4, 3.9))
y = 0; ticks = []; labels = []; heads = []
for gname, rows in G:
    heads.append((y - 0.55, gname)); 
    for name, n, adm in rows:
        r = adm / n
        ax.barh(y, r, height=0.62, color=BAR, edgecolor="none", zorder=3)
        ax.text(1.03, y, f"{adm:,} of {n:,}", va="center", ha="left", color=INK, fontsize=7.2)
        ticks.append(y); labels.append(name); y += 1
    y += 0.9
for yy, g in heads:
    ax.text(-0.235, yy - 0.15, g, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=8, fontweight="bold", color=INK)
ax.axvline(OVERALL, color=INK, lw=0.9, ls=(0, (4, 2)), zorder=4)
ax.text(OVERALL, -1.45, "All rows: 6,434 of 9,334 (68.9%)", ha="center", va="bottom", fontsize=7.2, color=INK)
ax.set_yticks(ticks); ax.set_yticklabels(labels, color=INK)
ax.set_ylim(y - 1.3, -1.5); ax.set_xlim(0, 1)
ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100"], color=MUTED)
ax.set_xlabel("Rows admitted by the gate (%)", color=INK)
ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(MUTED); ax.tick_params(axis="y", length=0, pad=4); ax.tick_params(axis="x", color=MUTED, length=2)
fig.subplots_adjust(left=0.20, right=0.74, top=0.97, bottom=0.11)
OUT = Path(__file__).resolve().parent
fig.savefig(OUT / "Fig1.pdf")
