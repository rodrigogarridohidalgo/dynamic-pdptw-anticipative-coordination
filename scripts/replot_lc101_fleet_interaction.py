import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

INPUT = Path(__file__).resolve().parents[1] / "results/optimization/lc101_joint_vs_sequential_dense.csv"
OUTDIR = Path(__file__).resolve().parents[1] / "results/figures"
OUTDIR.mkdir(exist_ok=True)

TOL = 1e-6

# ------------------------------------------------------------
# Read data
# ------------------------------------------------------------

with open(INPUT) as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["m"] = int(r["m"])
    r["alpha"] = float(r["alpha"])
    r["W_joint"] = float(r["W_joint"])
    r["W_sep"] = float(r["W_sep"])

ms = sorted(set(r["m"] for r in rows))
alphas = sorted(set(r["alpha"] for r in rows))

m_index = {m: i for i, m in enumerate(ms)}
a_index = {a: i for i, a in enumerate(alphas)}

# ------------------------------------------------------------
# Residual gap G_inf(alpha), using m=53
# ------------------------------------------------------------

G_inf = {}

for alpha in alphas:
    ref = next(
        r for r in rows
        if r["alpha"] == alpha and r["m"] == 53
    )

    G_inf[alpha] = (
        ref["W_joint"] - ref["W_sep"]
    )

# ------------------------------------------------------------
# Fleet-interaction matrix
# ------------------------------------------------------------

IF = np.zeros((len(alphas), len(ms)))

for r in rows:

    i = a_index[r["alpha"]]
    j = m_index[r["m"]]

    G = r["W_joint"] - r["W_sep"]

    IF[i, j] = (
        G - G_inf[r["alpha"]]
    )

vmin = float(IF.min())
vmax = float(IF.max())

print("I_F min =", round(vmin, 6))
print("I_F max =", round(vmax, 6))

# ------------------------------------------------------------
# Diverging normalization centered at zero
# ------------------------------------------------------------

norm = TwoSlopeNorm(
    vmin=vmin,
    vcenter=0.0,
    vmax=vmax
)

fig, ax = plt.subplots(figsize=(10, 5.8))

im = ax.imshow(
    IF,
    origin="lower",
    aspect="auto",
    extent=[
        min(ms) - 0.5,
        max(ms) + 0.5,
        min(alphas) - 0.05,
        max(alphas) + 0.05,
    ],
    cmap="coolwarm",
    norm=norm
)

cbar = fig.colorbar(im, ax=ax)

cbar.set_label(
    r"$I_F(m,\alpha)=G(m,\alpha)-G_\infty(\alpha)$"
)

ax.set_xlabel("Fleet size $m$")
ax.set_ylabel(r"$\alpha$")

ax.set_title(
    r"Fleet interaction with the anticipative gap"
)

ax.set_xticks(
    [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 53]
)

ax.set_yticks(alphas)

# Zero contour
X, Y = np.meshgrid(ms, alphas)

ax.contour(
    X,
    Y,
    IF,
    levels=[0.0],
    colors="black",
    linewidths=0.8
)

fig.tight_layout()

png = OUTDIR / "figure3_fleet_interaction_diverging.png"
pdf = OUTDIR / "figure3_fleet_interaction_diverging.pdf"

fig.savefig(
    png,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    pdf,
    bbox_inches="tight"
)

plt.close(fig)

print("Saved:")
print(png)
print(pdf)
