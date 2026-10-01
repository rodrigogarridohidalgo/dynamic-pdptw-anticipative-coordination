#!/usr/bin/env python
from pathlib import Path
from math import hypot
from collections import defaultdict
import csv
import statistics
import argparse

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

def serve(nodes, start_node, start_time, r):
    p = nodes[r["pickup"]]
    d = nodes[r["delivery"]]

    start_p = max(
        start_time + dist(start_node, p),
        r["release_time"],
        p["ready"],
    )
    if start_p > p["due"]:
        return None

    start_d = max(
        start_p + p["service"] + dist(p, d),
        d["ready"],
    )
    if start_d > d["due"]:
        return None

    return start_d + d["service"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="lc101")
    ap.add_argument("--dod-tag", default="050")
    ap.add_argument("--seed", type=int, default=20261001)
    args = ap.parse_args()

    raw = ROOT / "data" / "raw" / f"{args.instance}.txt"
    dyn = ROOT / "data" / "derived" / f"{args.instance}_dynamic_dod{args.dod_tag}_seed{args.seed}.csv"
    out = ROOT / "results" / "compatibility" / f"{args.instance}_transitions.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    nodes = load_nodes(raw)
    depot = nodes[0]

    with dyn.open() as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["pickup"] = int(r["pickup"])
        r["delivery"] = int(r["delivery"])
        r["dynamic"] = int(r["dynamic"])
        r["release_time"] = float(r["release_time"])

    J = [r for r in rows if r["dynamic"] == 0]
    K = [r for r in rows if r["dynamic"] == 1]

    first_finish = {}
    for j in J:
        f = serve(nodes, depot, 0.0, j)
        if f is not None:
            first_finish[j["pickup"]] = f

    transitions = []
    succ = defaultdict(list)
    pred = defaultdict(list)

    for j in J:
        jp = j["pickup"]
        if jp not in first_finish:
            continue

        end_j = nodes[j["delivery"]]

        for k in K:
            fk = serve(nodes, end_j, first_finish[jp], k)
            if fk is not None:
                kp = k["pickup"]
                transitions.append({
                    "j": jp,
                    "k": kp,
                    "finish_j": first_finish[jp],
                    "finish_k": fk,
                })
                succ[jp].append(kp)
                pred[kp].append(jp)

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["j", "k", "finish_j", "finish_k"])
        writer.writeheader()
        writer.writerows(transitions)

    counts = [len(succ[j["pickup"]]) for j in J if j["pickup"] in first_finish]
    total = len(first_finish) * len(K)
    distinct_sets = len({
        frozenset(succ[j["pickup"]])
        for j in J if j["pickup"] in first_finish
    })

    print(f"Saved: {out}")
    print("|J| =", len(J))
    print("|K| =", len(K))
    print("first-stage feasible j =", len(first_finish))
    print(
        "|U_j| min / median / mean / max =",
        min(counts),
        statistics.median(counts),
        round(statistics.mean(counts), 2),
        max(counts),
    )
    print("J with >=1 successor =", sum(c > 0 for c in counts))
    print("K reachable from >=1 J =", sum(len(pred[k["pickup"]]) > 0 for k in K))
    print("distinct successor sets =", distinct_sets)
    print("transitions =", len(transitions), "/", total)
    print("transition density =", round(len(transitions) / total, 4))

if __name__ == "__main__":
    main()
