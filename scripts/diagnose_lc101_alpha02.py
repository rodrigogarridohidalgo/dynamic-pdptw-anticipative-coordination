import csv
import numpy as np

from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix

FILE = "lc101_two_stage_economics.csv"

ALPHA = 0.2
M = 53
TOL = 1e-8

# ------------------------------------------------------------
# Read economics
# ------------------------------------------------------------

with open(FILE) as f:
    rows = list(csv.DictReader(f))

J_rows = [
    r for r in rows
    if r["type"] == "J"
]

K_rows = [
    r for r in rows
    if r["type"] == "K"
    and int(r["feasible"]) == 1
]

JK_rows = [
    r for r in rows
    if r["type"] == "JK"
    and int(r["feasible"]) == 1
]

J = sorted(int(r["j"]) for r in J_rows)
K = sorted(int(r["k"]) for r in K_rows)

j_pos = {j: i for i, j in enumerate(J)}
k_pos = {k: i for i, k in enumerate(K)}

econ_J = {
    int(r["j"]): {
        "A": float(r["A"]),
        "B": float(r["B"]),
    }
    for r in J_rows
}

econ_K = {
    int(r["k"]): {
        "A": float(r["A"]),
        "B": float(r["B"]),
    }
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

def value(A, B):
    return ALPHA * B - A

# ------------------------------------------------------------
# Joint MILP
#
# variables:
# J only
# K only
# JK chain
# ------------------------------------------------------------

nJ = len(J)
nK = len(K)
nC = len(chains)

off_J = 0
off_K = nJ
off_C = nJ + nK

nvar = nJ + nK + nC

values = np.zeros(nvar)

for i, j in enumerate(J):
    e = econ_J[j]
    values[off_J + i] = value(e["A"], e["B"])

for i, k in enumerate(K):
    e = econ_K[k]
    values[off_K + i] = value(e["A"], e["B"])

for q, ch in enumerate(chains):
    values[off_C + q] = value(
        ch["A"],
        ch["B"]
    )

# ------------------------------------------------------------
# Constraints
# ------------------------------------------------------------

nrows = nJ + nK + 1
Acon = lil_matrix((nrows, nvar), dtype=float)

# each J at most once
for i, j in enumerate(J):
    Acon[i, off_J + i] = 1.0

# each K at most once
for i, k in enumerate(K):
    Acon[nJ + i, off_K + i] = 1.0

# chains consume their J and K
for q, ch in enumerate(chains):

    ji = j_pos[ch["j"]]
    ki = k_pos[ch["k"]]

    Acon[ji, off_C + q] = 1.0
    Acon[nJ + ki, off_C + q] = 1.0

# fleet
Acon[nJ + nK, :] = 1.0

lower = np.full(nrows, -np.inf)
upper = np.ones(nrows)

upper[-1] = M

constraint = LinearConstraint(
    Acon.tocsr(),
    lower,
    upper
)

res = milp(
    c=-values,
    integrality=np.ones(nvar, dtype=int),
    bounds=Bounds(
        np.zeros(nvar),
        np.ones(nvar)
    ),
    constraints=constraint,
    options={"disp": False},
)

if not res.success:
    raise RuntimeError(res.message)

x = np.rint(res.x).astype(int)

W = float(values @ x)

# ------------------------------------------------------------
# Selected alternatives
# ------------------------------------------------------------

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
    chains[q]
    for q in range(nC)
    if x[off_C + q]
]

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=== LC101 joint diagnostic ===")
print("alpha =", ALPHA)
print("fleet =", M)
print("W_joint =", round(W, 6))
print("J-only =", len(selected_J))
print("K-only =", len(selected_K))
print("JK =", len(selected_JK))
print("vehicles used =", len(selected_J) + len(selected_K) + len(selected_JK))

print("\n=== selected JK chains ===")

records = []

for ch in selected_JK:

    j = ch["j"]
    k = ch["k"]

    ej = econ_J[j]
    ek = econ_K[k]

    vj = value(ej["A"], ej["B"])
    vk = value(ek["A"], ek["B"])
    vjk = value(ch["A"], ch["B"])

    chain_gain = vjk - (vj + vk)

    optional_gain = (
        vjk
        - max(vj, 0.0)
        - max(vk, 0.0)
    )

    if vj <= 0 and vjk > 0:
        mechanism = "bridge: j unattractive alone"
    elif vk <= 0 and vjk > 0:
        mechanism = "bridge: k unattractive alone"
    elif vj > 0 and vk > 0 and chain_gain > TOL:
        mechanism = "repositioning complementarity"
    else:
        mechanism = "other"

    records.append({
        "j": j,
        "k": k,
        "vj": vj,
        "vk": vk,
        "vjk": vjk,
        "chain_gain": chain_gain,
        "optional_gain": optional_gain,
        "mechanism": mechanism,
    })

records.sort(
    key=lambda r: r["vjk"],
    reverse=True
)

for r in records:

    print(
        f"j={r['j']:3d} "
        f"k={r['k']:3d}  "
        f"v_j={r['vj']:9.3f}  "
        f"v_k={r['vk']:9.3f}  "
        f"v_jk={r['vjk']:9.3f}  "
        f"Delta_chain={r['chain_gain']:9.3f}  "
        f"Delta_opt={r['optional_gain']:9.3f}  "
        f"{r['mechanism']}"
    )

# ------------------------------------------------------------
# Aggregate mechanism decomposition
# ------------------------------------------------------------

bridge_j = [
    r for r in records
    if r["vj"] <= 0 and r["vjk"] > 0
]

bridge_k = [
    r for r in records
    if r["vk"] <= 0 and r["vjk"] > 0
]

both_positive = [
    r for r in records
    if r["vj"] > 0 and r["vk"] > 0
]

print("\n=== mechanism summary ===")

print(
    "chains with j <= 0 but jk > 0 =",
    len(bridge_j)
)

print(
    "chains with k <= 0 but jk > 0 =",
    len(bridge_k)
)

print(
    "chains with both singles > 0 =",
    len(both_positive)
)

print(
    "sum Delta_chain =",
    round(
        sum(r["chain_gain"] for r in records),
        3
    )
)

print(
    "sum Delta_opt =",
    round(
        sum(r["optional_gain"] for r in records),
        3
    )
)

# ------------------------------------------------------------
# J-only and K-only
# ------------------------------------------------------------

print("\n=== selected J-only ===")

for j in selected_J:
    e = econ_J[j]
    print(
        f"j={j:3d} "
        f"value={value(e['A'], e['B']):9.3f}"
    )

print("\n=== selected K-only ===")

for k in selected_K:
    e = econ_K[k]
    print(
        f"k={k:3d} "
        f"value={value(e['A'], e['B']):9.3f}"
    )
