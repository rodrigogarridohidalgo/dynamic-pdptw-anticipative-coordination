import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "results/optimization/lc101_joint_vs_sequential_dense.csv"

TOL = 1e-6

with open(FILE) as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["m"] = int(r["m"])
    r["alpha"] = float(r["alpha"])
    r["W_joint"] = float(r["W_joint"])
    r["W_sep"] = float(r["W_sep"])

by_alpha = defaultdict(list)

for r in rows:
    by_alpha[r["alpha"]].append(r)

print(
    "alpha  "
    "mJ_sat  mS_sat  "
    "G_inf     Psi_inf   "
    "max_Psi   m@maxPsi  "
    "max_IF     m@maxIF"
)

print("-" * 92)

for alpha in sorted(by_alpha):

    rr = sorted(
        by_alpha[alpha],
        key=lambda x: x["m"]
    )

    ref = next(r for r in rr if r["m"] == 53)

    WJ_inf = ref["W_joint"]
    WS_inf = ref["W_sep"]

    G_inf = WJ_inf - WS_inf

    Psi_inf = (
        1.0 - WS_inf / WJ_inf
        if WJ_inf > TOL
        else 0.0
    )

    # Smallest fleet at which objective reaches its
    # m=53 value.
    mJ_sat = next(
        r["m"]
        for r in rr
        if abs(r["W_joint"] - WJ_inf) <= TOL
    )

    mS_sat = next(
        r["m"]
        for r in rr
        if abs(r["W_sep"] - WS_inf) <= TOL
    )

    enriched = []

    for r in rr:

        G = r["W_joint"] - r["W_sep"]

        Psi = (
            1.0 - r["W_sep"] / r["W_joint"]
            if r["W_joint"] > TOL
            else 0.0
        )

        IF = G - G_inf

        enriched.append({
            "m": r["m"],
            "G": G,
            "Psi": Psi,
            "IF": IF,
        })

    max_psi = max(
        enriched,
        key=lambda x: x["Psi"]
    )

    max_if = max(
        enriched,
        key=lambda x: x["IF"]
    )

    print(
        f"{alpha:4.1f}  "
        f"{mJ_sat:6d}  "
        f"{mS_sat:6d}  "
        f"{G_inf:8.3f}  "
        f"{100*Psi_inf:8.3f}%  "
        f"{100*max_psi['Psi']:8.3f}%  "
        f"{max_psi['m']:8d}  "
        f"{max_if['IF']:8.3f}  "
        f"{max_if['m']:7d}"
    )
