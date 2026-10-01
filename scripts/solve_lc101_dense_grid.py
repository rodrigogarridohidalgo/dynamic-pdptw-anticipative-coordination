import csv
import math
from pathlib import Path

try:
    import numpy as np
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
except ImportError:
    raise SystemExit(
        "\nEste script requiere numpy y scipy.\n"
        "Instala con:\n"
        "  python3 -m pip install numpy scipy\n"
        "y vuelve a ejecutarlo.\n"
    )

INPUT = Path(__file__).resolve().parents[1] / "results/economics/lc101_two_stage_economics.csv"
OUTPUT = Path(__file__).resolve().parents[1] / "results/optimization/lc101_joint_vs_sequential_dense.csv"

FLEETS = list(range(1, 54))
ALPHAS = [round(0.1 * i, 10) for i in range(1, 16)]

TOL = 1e-7

# ============================================================
# Read economics
# ============================================================

with open(INPUT) as f:
    rows = list(csv.DictReader(f))

J_rows = [r for r in rows if r["type"] == "J"]
K_rows = [
    r for r in rows
    if r["type"] == "K" and int(r["feasible"]) == 1
]
JK_rows = [
    r for r in rows
    if r["type"] == "JK" and int(r["feasible"]) == 1
]

J = sorted(int(r["j"]) for r in J_rows)
K = sorted(int(r["k"]) for r in K_rows)

j_pos = {j: i for i, j in enumerate(J)}
k_pos = {k: i for i, k in enumerate(K)}

econ_J = {
    int(r["j"]): (float(r["A"]), float(r["B"]))
    for r in J_rows
}

econ_K = {
    int(r["k"]): (float(r["A"]), float(r["B"]))
    for r in K_rows
}

chains = []

for r in JK_rows:
    chains.append({
        "j": int(r["j"]),
        "k": int(r["k"]),
        "A": float(r["A"]),
        "B": float(r["B"]),
    })

print("=== input ===")
print("|J| =", len(J))
print("|K feasible from depot| =", len(K))
print("|JK| =", len(chains))
print("fleets =", FLEETS)
print("alphas =", ALPHAS)


# ============================================================
# Utility
# ============================================================

def utility(A, B, alpha):
    return alpha * B - A


# ============================================================
# Generic MILP solver
# scipy.optimize.milp minimizes c'x
# ============================================================

def solve_binary(c, constraints):

    n = len(c)

    result = milp(
        c=np.asarray(c, dtype=float),
        integrality=np.ones(n, dtype=int),
        bounds=Bounds(
            np.zeros(n),
            np.ones(n)
        ),
        constraints=constraints,
        options={"disp": False},
    )

    if not result.success:
        raise RuntimeError(
            f"MILP failed: {result.message}"
        )

    x = np.rint(result.x).astype(int)

    return result, x


# ============================================================
# JOINT
#
# variables:
#   a_j   = serve j only
#   b_k   = serve k only
#   c_jk  = serve chain j -> k
#
# Each selected variable consumes one vehicle.
# ============================================================

def solve_joint(alpha, m):

    nJ = len(J)
    nK = len(K)
    nC = len(chains)

    off_J = 0
    off_K = nJ
    off_C = nJ + nK

    nvar = nJ + nK + nC

    values = np.zeros(nvar)

    for i, j in enumerate(J):
        A, B = econ_J[j]
        values[off_J + i] = utility(A, B, alpha)

    for i, k in enumerate(K):
        A, B = econ_K[k]
        values[off_K + i] = utility(A, B, alpha)

    for q, ch in enumerate(chains):
        values[off_C + q] = utility(
            ch["A"], ch["B"], alpha
        )

    # Constraints:
    # each j <= 1
    # each k <= 1
    # vehicles <= m

    nrows = nJ + nK + 1
    Acon = lil_matrix((nrows, nvar), dtype=float)

    # J-only variables
    for i, j in enumerate(J):
        Acon[i, off_J + i] = 1.0

    # K-only variables
    for i, k in enumerate(K):
        Acon[nJ + i, off_K + i] = 1.0

    # JK chains
    for q, ch in enumerate(chains):

        jj = j_pos[ch["j"]]
        kk = k_pos[ch["k"]]

        Acon[jj, off_C + q] = 1.0
        Acon[nJ + kk, off_C + q] = 1.0

    # fleet
    Acon[nJ + nK, :] = 1.0

    lower = np.full(nrows, -np.inf)
    upper = np.ones(nrows)

    upper[-1] = m

    constraint = LinearConstraint(
        Acon.tocsr(),
        lower,
        upper
    )

    # maximize values -> minimize -values
    result, x = solve_binary(
        -values,
        constraint
    )

    W = float(values @ x)

    selected_J = [
        J[i]
        for i in range(nJ)
        if x[off_J + i]
    ]

    selected_K = [
        K[i]
        for i in range(nK)
        if x[off_K + i]
    ]

    selected_JK = [
        (chains[q]["j"], chains[q]["k"])
        for q in range(nC)
        if x[off_C + q]
    ]

    used = (
        len(selected_J)
        + len(selected_K)
        + len(selected_JK)
    )

    return {
        "W": W,
        "used": used,
        "J": selected_J,
        "K": selected_K,
        "JK": selected_JK,
    }


# ============================================================
# SEQUENTIAL
#
# Stage 1:
# x_j = commitment to serve j.
#
# maximize sum_j v_j x_j
# s.t. sum x_j <= m.
#
# Stage 2:
# among ALL stage-1 optima, maximize final two-stage value.
#
# Final variables:
# a_j  = committed j remains J-only
# b_k  = idle vehicle serves k
# c_jk = committed j continues to k
#
# linking:
# a_j + sum_k c_jk = x_j
# ============================================================

def solve_stage1_value(alpha, m):

    vals = np.array([
        utility(
            econ_J[j][0],
            econ_J[j][1],
            alpha
        )
        for j in J
    ])

    # Since only a cardinality restriction exists,
    # solve directly and exactly.
    positive = sorted(
        [v for v in vals if v > TOL],
        reverse=True
    )

    W1 = sum(positive[:m])

    return float(W1), vals


def solve_sequential(alpha, m):

    W1_star, stage1_vals = solve_stage1_value(
        alpha, m
    )

    nJ = len(J)
    nK = len(K)
    nC = len(chains)

    # variables:
    # x_j : stage-1 commitment
    # a_j : final J-only
    # b_k : final K-only
    # c_jk: final chain

    off_x = 0
    off_a = nJ
    off_b = 2 * nJ
    off_c = 2 * nJ + nK

    nvar = 2 * nJ + nK + nC

    final_values = np.zeros(nvar)

    # x has no direct final contribution

    for i, j in enumerate(J):
        A, B = econ_J[j]
        final_values[off_a + i] = utility(
            A, B, alpha
        )

    for i, k in enumerate(K):
        A, B = econ_K[k]
        final_values[off_b + i] = utility(
            A, B, alpha
        )

    for q, ch in enumerate(chains):
        final_values[off_c + q] = utility(
            ch["A"], ch["B"], alpha
        )

    # Constraints:
    #
    # 1. for each j:
    #    a_j + sum_k c_jk - x_j = 0
    #
    # 2. for each k:
    #    b_k + sum_j c_jk <= 1
    #
    # 3. stage-1 fleet:
    #    sum x_j <= m
    #
    # 4. final fleet:
    #    sum a_j + sum b_k + sum c_jk <= m
    #
    # 5. stage-1 objective fixed at W1*
    #    sum v_j x_j = W1*

    nrows = nJ + nK + 3

    Acon = lil_matrix(
        (nrows, nvar),
        dtype=float
    )

    lower = np.full(nrows, -np.inf)
    upper = np.full(nrows, np.inf)

    # --------------------------------------------------------
    # j linking equality
    # --------------------------------------------------------

    for i, j in enumerate(J):

        row = i

        Acon[row, off_x + i] = -1.0
        Acon[row, off_a + i] = 1.0

        lower[row] = 0.0
        upper[row] = 0.0

    for q, ch in enumerate(chains):

        jj = j_pos[ch["j"]]

        Acon[jj, off_c + q] = 1.0

    # --------------------------------------------------------
    # k exclusivity
    # --------------------------------------------------------

    for i, k in enumerate(K):

        row = nJ + i

        Acon[row, off_b + i] = 1.0

        lower[row] = -np.inf
        upper[row] = 1.0

    for q, ch in enumerate(chains):

        kk = k_pos[ch["k"]]
        row = nJ + kk

        Acon[row, off_c + q] = 1.0

    # --------------------------------------------------------
    # stage-1 fleet
    # --------------------------------------------------------

    row_stage1_fleet = nJ + nK

    for i in range(nJ):
        Acon[
            row_stage1_fleet,
            off_x + i
        ] = 1.0

    lower[row_stage1_fleet] = -np.inf
    upper[row_stage1_fleet] = m

    # --------------------------------------------------------
    # final fleet
    # --------------------------------------------------------

    row_final_fleet = nJ + nK + 1

    for i in range(nJ):
        Acon[
            row_final_fleet,
            off_a + i
        ] = 1.0

    for i in range(nK):
        Acon[
            row_final_fleet,
            off_b + i
        ] = 1.0

    for q in range(nC):
        Acon[
            row_final_fleet,
            off_c + q
        ] = 1.0

    lower[row_final_fleet] = -np.inf
    upper[row_final_fleet] = m

    # --------------------------------------------------------
    # lexicographic stage-1 optimum
    # --------------------------------------------------------

    row_stage1_value = nJ + nK + 2

    for i in range(nJ):
        Acon[
            row_stage1_value,
            off_x + i
        ] = stage1_vals[i]

    # small numerical tolerance around W1*
    eps = max(
        1e-7,
        1e-8 * max(1.0, abs(W1_star))
    )

    lower[row_stage1_value] = W1_star - eps
    upper[row_stage1_value] = W1_star + eps

    constraint = LinearConstraint(
        Acon.tocsr(),
        lower,
        upper
    )

    result, x = solve_binary(
        -final_values,
        constraint
    )

    Wsep = float(final_values @ x)

    selected_stage1 = [
        J[i]
        for i in range(nJ)
        if x[off_x + i]
    ]

    selected_J = [
        J[i]
        for i in range(nJ)
        if x[off_a + i]
    ]

    selected_K = [
        K[i]
        for i in range(nK)
        if x[off_b + i]
    ]

    selected_JK = [
        (chains[q]["j"], chains[q]["k"])
        for q in range(nC)
        if x[off_c + q]
    ]

    used = (
        len(selected_J)
        + len(selected_K)
        + len(selected_JK)
    )

    return {
        "W1": W1_star,
        "W": Wsep,
        "used": used,
        "stage1": selected_stage1,
        "J": selected_J,
        "K": selected_K,
        "JK": selected_JK,
    }


# ============================================================
# Main experiment
# ============================================================

results = []

print("\n=== JOINT vs SEQUENTIAL ===")

for m in FLEETS:

    print(f"\n---------- fleet m={m} ----------")

    for alpha in ALPHAS:

        joint = solve_joint(alpha, m)
        sep = solve_sequential(alpha, m)

        Wj = joint["W"]
        Ws = sep["W"]

        # The sequential completed plan must be feasible
        # for the joint problem.
        if Ws > Wj + 1e-5:
            raise RuntimeError(
                f"W_sep > W_joint at "
                f"m={m}, alpha={alpha}: "
                f"{Ws} > {Wj}"
            )

        if Wj > TOL:
            psi = 1.0 - Ws / Wj
        else:
            psi = math.nan

        results.append({
            "m": m,
            "alpha": alpha,
            "W1": sep["W1"],
            "W_joint": Wj,
            "W_sep": Ws,
            "Psi_S": psi,
            "Psi_S_pct":
                100.0 * psi
                if not math.isnan(psi)
                else "",
            "joint_used": joint["used"],
            "sep_used": sep["used"],
            "stage1_selected":
                len(sep["stage1"]),
            "joint_J_only":
                len(joint["J"]),
            "joint_K_only":
                len(joint["K"]),
            "joint_JK":
                len(joint["JK"]),
            "sep_J_only":
                len(sep["J"]),
            "sep_K_only":
                len(sep["K"]),
            "sep_JK":
                len(sep["JK"]),
        })

        psi_text = (
            "   NA"
            if math.isnan(psi)
            else f"{100*psi:6.2f}%"
        )

        print(
            f"alpha={alpha:3.1f}  "
            f"Wjoint={Wj:10.3f}  "
            f"Wsep={Ws:10.3f}  "
            f"Psi={psi_text}  "
            f"joint(JK)={len(joint['JK']):2d}  "
            f"sep(JK)={len(sep['JK']):2d}"
        )


# ============================================================
# Save results
# ============================================================

with open(OUTPUT, "w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=results[0].keys()
    )

    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved: {OUTPUT}")


# ============================================================
# Summary of maximum gaps
# ============================================================

print("\n=== maximum Psi_S by fleet ===")

for m in FLEETS:

    rr = [
        r for r in results
        if r["m"] == m
        and r["Psi_S_pct"] != ""
    ]

    best = max(
        rr,
        key=lambda r: r["Psi_S"]
    )

    print(
        f"m={m:2d}: "
        f"max Psi_S={100*best['Psi_S']:.3f}% "
        f"at alpha={best['alpha']:.1f}"
    )
