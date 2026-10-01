import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results/optimization/lc101_joint_vs_sequential.csv"
OUTPUT = ROOT / "results/optimization/lc101_gap_decomposition.csv"

with open(INPUT) as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["m"] = int(r["m"])
    r["alpha"] = float(r["alpha"])
    r["W_joint"] = float(r["W_joint"])
    r["W_sep"] = float(r["W_sep"])

# ------------------------------------------------------------
# Group by alpha
# ------------------------------------------------------------

by_alpha = defaultdict(list)

for r in rows:
    by_alpha[r["alpha"]].append(r)

results = []

print("=== LC101 gap decomposition ===")

for alpha in sorted(by_alpha):

    rr = sorted(
        by_alpha[alpha],
        key=lambda x: x["m"]
    )

    # m = 53 is our nonbinding-fleet reference
    ref = next(
        (r for r in rr if r["m"] == 53),
        None
    )

    if ref is None:
        raise RuntimeError(
            f"No m=53 reference for alpha={alpha}"
        )

    Wj_inf = ref["W_joint"]
    Ws_inf = ref["W_sep"]

    G_inf = Wj_inf - Ws_inf

    if Wj_inf > 0:
        Psi_inf = 1.0 - Ws_inf / Wj_inf
    else:
        Psi_inf = 0.0

    print(f"\n--- alpha={alpha:.1f} ---")
    print(
        f"G_inf={G_inf:.3f}  "
        f"Psi_inf={100*Psi_inf:.3f}%"
    )

    for r in rr:

        m = r["m"]
        Wj = r["W_joint"]
        Ws = r["W_sep"]

        G = Wj - Ws

        if Wj > 0:
            Psi = 1.0 - Ws / Wj
        else:
            Psi = 0.0

        I_fleet = G - G_inf

        # Fraction of finite-fleet absolute gap attributable
        # to the residual non-fleet component.
        if abs(G) > 1e-12:
            residual_share = G_inf / G
        else:
            residual_share = 0.0

        results.append({
            "alpha": alpha,
            "m": m,
            "W_joint": Wj,
            "W_sep": Ws,
            "G_total": G,
            "Psi_S": Psi,
            "Psi_S_pct": 100 * Psi,
            "G_infinity": G_inf,
            "Psi_infinity": Psi_inf,
            "Psi_infinity_pct": 100 * Psi_inf,
            "I_fleet": I_fleet,
            "residual_share_of_gap": residual_share,
        })

        sign = (
            "amplifies"
            if I_fleet > 1e-8
            else "attenuates"
            if I_fleet < -1e-8
            else "neutral"
        )

        print(
            f"m={m:2d}  "
            f"G={G:8.3f}  "
            f"G_inf={G_inf:8.3f}  "
            f"I_fleet={I_fleet:8.3f}  "
            f"Psi={100*Psi:6.2f}%  "
            f"{sign}"
        )

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

with open(OUTPUT, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved: {OUTPUT}")

# ------------------------------------------------------------
# Compact summary
# ------------------------------------------------------------

print("\n=== asymptotic residual gap ===")

for alpha in sorted(by_alpha):

    r = next(
        x for x in results
        if x["alpha"] == alpha
        and x["m"] == 53
    )

    print(
        f"alpha={alpha:.1f}  "
        f"G_inf={r['G_infinity']:.3f}  "
        f"Psi_inf={r['Psi_infinity_pct']:.3f}%"
    )

print("\n=== strongest fleet amplification ===")

for alpha in sorted(by_alpha):

    rr = [
        r for r in results
        if r["alpha"] == alpha
    ]

    best = max(
        rr,
        key=lambda x: x["I_fleet"]
    )

    print(
        f"alpha={alpha:.1f}  "
        f"m={best['m']:2d}  "
        f"I_fleet={best['I_fleet']:.3f}"
    )

print("\n=== strongest fleet attenuation ===")

for alpha in sorted(by_alpha):

    rr = [
        r for r in results
        if r["alpha"] == alpha
    ]

    worst = min(
        rr,
        key=lambda x: x["I_fleet"]
    )

    print(
        f"alpha={alpha:.1f}  "
        f"m={worst['m']:2d}  "
        f"I_fleet={worst['I_fleet']:.3f}"
    )
