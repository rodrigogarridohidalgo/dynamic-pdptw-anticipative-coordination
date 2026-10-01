#!/usr/bin/env python
from pathlib import Path
from collections import deque
import csv
import statistics
import argparse

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="lc101")
    args = ap.parse_args()

    inp = ROOT / "results" / "compatibility" / f"{args.instance}_transitions.csv"
    out_nodes = ROOT / "results" / "conflict_graph" / f"{args.instance}_conflict_nodes.csv"
    out_edges = ROOT / "results" / "conflict_graph" / f"{args.instance}_conflict_edges.csv"
    out_nodes.parent.mkdir(parents=True, exist_ok=True)

    with inp.open() as f:
        transitions = list(csv.DictReader(f))

    chains = [
        {"id": i, "j": int(r["j"]), "k": int(r["k"])}
        for i, r in enumerate(transitions)
    ]

    n = len(chains)
    adj = [set() for _ in range(n)]
    edges = []

    for a in range(n):
        pa = chains[a]
        for b in range(a + 1, n):
            pb = chains[b]
            if pa["j"] == pb["j"] or pa["k"] == pb["k"]:
                adj[a].add(b)
                adj[b].add(a)
                edges.append((a, b))

    degrees = [len(s) for s in adj]

    seen = set()
    components = []

    for start in range(n):
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp = []

        while q:
            u = q.popleft()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        components.append(comp)

    with out_nodes.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "j", "k", "degree"])
        writer.writeheader()
        for p, d in zip(chains, degrees):
            writer.writerow({**p, "degree": d})

    with out_edges.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        writer.writerows(edges)

    density = 2 * len(edges) / (n * (n - 1)) if n > 1 else 0.0

    print("nodes =", n)
    print("edges =", len(edges))
    print("density =", round(density, 5))
    print(
        "degree min / median / mean / max =",
        min(degrees),
        statistics.median(degrees),
        round(statistics.mean(degrees), 2),
        max(degrees),
    )
    print("distinct degrees =", len(set(degrees)))
    print("connected components =", len(components))
    print("largest component =", max(len(c) for c in components))
    print("Saved:", out_nodes)
    print("Saved:", out_edges)

if __name__ == "__main__":
    main()
