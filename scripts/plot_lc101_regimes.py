import csv
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

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

# matrices: rows = alpha, columns = m
Psi = np.zeros((len(alphas), len(ms)))
Gap = np.zeros_like(Psi)
IF = np.zeros_like(Psi)

# ------------------------------------------------------------
# Asymptotic reference m=53 for each alpha
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
# Fill matrices
# ------------------------------------------------------------

for r in rows:

    i = a_index[r["alpha"]]
    j = m_index[r["m"]]

    Wj = r["W_joint"]
    Ws = r["W_sep"]

    gap = Wj - Ws

    if Wj > TOL:
        psi = 100.0 * (1.0 - Ws / Wj)
    else:
        psi = 0.0

    Psi[i, j] = psi
    Gap[i, j] = gap
    IF[i, j] = gap - G_inf[r["alpha"]]

# ------------------------------------------------------------
# Helper for heatmaps
# ------------------------------------------------------------

def heatmap(Z, title, cbar_label, stem):

    fig, ax = plt.subplots(figsize=(10, 5.8))

    im = ax.imshow(
        Z,
        origin="lower",
        aspect="auto",
        extent=[
            min(ms) - 0.5,
            max(ms) + 0.5,
            min(alphas) - 0.05,
            max(alphas) + 0.05,
        ]
    )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)

    ax.set_xlabel("Fleet size $m$")
    ax.set_ylabel(r"$\alpha$")
    ax.set_title(title)

    ax.set_xticks(
        [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 53]
    )

    ax.set_yticks(alphas)

    fig.tight_layout()

    fig.savefig(
        OUTDIR / f"{stem}.png",
        dpi=300,
        bbox_inches="tight"
    )

    fig.savefig(
        OUTDIR / f"{stem}.pdf",
        bbox_inches="tight"
    )

    plt.close(fig)


# ------------------------------------------------------------
# Figure 1: relative sequential loss
# ------------------------------------------------------------

heatmap(
    Psi,
    r"Relative value of anticipative coordination: $\Psi_S(m,\alpha)$",
    r"$\Psi_S$ (%)",
    "figure1_psi_heatmap"
)

# ------------------------------------------------------------
# Figure 2: absolute gap
# ------------------------------------------------------------

heatmap(
    Gap,
    r"Absolute anticipative gap: $G(m,\alpha)$",
    r"$G=W^{joint}-W^{sep}$",
    "figure2_gap_heatmap"
)

# ------------------------------------------------------------
# Figure 3: fleet interaction
# ------------------------------------------------------------

heatmap(
    IF,
    r"Fleet-interaction term: $I_F(m,\alpha)$",
    r"$I_F=G(m,\alpha)-G_\infty(\alpha)$",
    "figure3_fleet_interaction_heatmap"
)

# ------------------------------------------------------------
# Figure 4: saturation fleet by alpha
# ------------------------------------------------------------

by_alpha = defaultdict(list)

for r in rows:
    by_alpha[r["alpha"]].append(r)

mJ_sat = []
mS_sat = []

for alpha in alphas:

    rr = sorted(
        by_alpha[alpha],
        key=lambda x: x["m"]
    )

    ref = next(
        r for r in rr
        if r["m"] == 53
    )

    WJ_inf = ref["W_joint"]
    WS_inf = ref["W_sep"]

    mj = next(
        r["m"]
        for r in rr
        if abs(r["W_joint"] - WJ_inf) <= TOL
    )

    msat = next(
        r["m"]
        for r in rr
        if abs(r["W_sep"] - WS_inf) <= TOL
    )

    mJ_sat.append(mj)
    mS_sat.append(msat)

fig, ax = plt.subplots(figsize=(8, 5.5))

ax.plot(
    alphas,
    mJ_sat,
    marker="o",
    label=r"Joint: $m_J^{sat}$"
)

ax.plot(
    alphas,
    mS_sat,
    marker="s",
    label=r"Sequential: $m_S^{sat}$"
)

ax.set_xlabel(r"$\alpha$")
ax.set_ylabel("Saturation fleet size")
ax.set_title("Fleet size required to reach the unconstrained value")
ax.set_xticks(alphas)
ax.legend()

fig.tight_layout()

fig.savefig(
    OUTDIR / "figure4_saturation_fleet.png",
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    OUTDIR / "figure4_saturation_fleet.pdf",
    bbox_inches="tight"
)

plt.close(fig)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("Saved figures in:", OUTDIR)

for p in sorted(OUTDIR.iterdir()):
    print(" ", p)

print("\nSaturation thresholds:")
print("alpha   mJ_sat   mS_sat")

for a, mj, msat in zip(
    alphas,
    mJ_sat,
    mS_sat
):
    print(
        f"{a:4.1f}   "
        f"{mj:6d}   "
        f"{msat:6d}"
    )
