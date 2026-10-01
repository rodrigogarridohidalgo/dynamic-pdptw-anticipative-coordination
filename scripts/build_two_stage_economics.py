#!/usr/bin/env python
from pathlib import Path
from math import hypot
import csv
import argparse
import statistics

ROOT = Path(__file__).resolve().parents[1]

def load_nodes(path):
    lines = [x.strip() for x in path.read_text().splitlines() if x.strip()]
    data = [list(map(float, x.split())) for x in lines[1:]]

    nodes = {}
    for row in data:
        i = int(row[0])
        nodes[i] = {
            "x": row[1],
            "y": row[2],
            "ready": row[4],
            "due": row[5],
            "service": row[6],
        }
    return nodes

def dist(a, b):
    return hypot(a["x"] - b["x"], a["y"] - b["y"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="lc101")
    ap.add_argument("--dod-tag", default="050")
    ap.add_argument("--seed", type=int, default=20261001)
    args = ap.parse_args()

    raw = ROOT / "data" / "raw" / f"{args.instance}.txt"
    dyn = ROOT / "data" / "derived" / f"{args.instance}_dynamic_dod{args.dod_tag}_seed{args.seed}.csv"
    trans = ROOT / "results" / "compatibility" / f"{args.instance}_transitions.csv"
    out = ROOT / "results" / "economics" / f"{args.instance}_two_stage_economics.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    nodes = load_nodes(raw)
    depot = nodes[0]

    with dyn.open() as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["pickup"] = int(r["pickup"])
        r["delivery"] = int(r["delivery"])
        r["q"] = float(r["q"])
        r["dynamic"] = int(r["dynamic"])

    J = {r["pickup"]: r for r in rows if r["dynamic"] == 0}
    K = {r["pickup"]: r for r in rows if r["dynamic"] == 1}

    with trans.open() as f:
        transitions = list(csv.DictReader(f))

    out_rows = []

    def single(r):
        p = nodes[r["pickup"]]
        d = nodes[r["delivery"]]
        A = dist(depot, p) + dist(p, d)
        B = r["q"] * dist(p, d)
        return A, B, (A / B if B > 0 else None)

    for j in J.values():
        A, B, a = single(j)
        out_rows.append({
            "type": "J", "j": j["pickup"], "k": "",
            "q_j": j["q"], "q_k": "",
            "A": A, "B": B, "alpha_star": a, "feasible": 1,
        })

    for k in K.values():
        A, B, a = single(k)
        out_rows.append({
            "type": "K", "j": "", "k": k["pickup"],
            "q_j": "", "q_k": k["q"],
            "A": A, "B": B, "alpha_star": a, "feasible": 1,
        })

    for tr in transitions:
        j = J[int(tr["j"])]
        k = K[int(tr["k"])]

        pj = nodes[j["pickup"]]
        dj = nodes[j["delivery"]]
        pk = nodes[k["pickup"]]
        dk = nodes[k["delivery"]]

        A = (
            dist(depot, pj)
            + dist(pj, dj)
            + dist(dj, pk)
            + dist(pk, dk)
        )
        B = (
            j["q"] * dist(pj, dj)
            + k["q"] * dist(pk, dk)
        )

        out_rows.append({
            "type": "JK", "j": j["pickup"], "k": k["pickup"],
            "q_j": j["q"], "q_k": k["q"],
            "A": A, "B": B,
            "alpha_star": (A / B if B > 0 else None),
            "feasible": 1,
        })

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["type", "j", "k", "q_j", "q_k", "A", "B", "alpha_star", "feasible"],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print("Saved:", out)
    print("|J| =", len(J))
    print("|K| =", len(K))
    print("|JK| =", len(transitions))

if __name__ == "__main__":
    main()
