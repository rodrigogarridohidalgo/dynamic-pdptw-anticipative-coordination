#!/usr/bin/env python
from pathlib import Path
from math import hypot
import random
import csv
import argparse

ROOT = Path(__file__).resolve().parents[1]

def load_instance(path):
    lines = [x.strip() for x in path.read_text().splitlines() if x.strip()]
    header = list(map(float, lines[0].split()))
    data = [list(map(float, x.split())) for x in lines[1:]]

    nodes = {}
    for row in data:
        i = int(row[0])
        nodes[i] = {
            "x": row[1],
            "y": row[2],
            "demand": row[3],
            "ready": row[4],
            "due": row[5],
            "service": row[6],
            "pickup_link": int(row[7]),
            "delivery_link": int(row[8]),
        }
    return header, nodes

def dist(a, b):
    return hypot(a["x"] - b["x"], a["y"] - b["y"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="lc101")
    ap.add_argument("--dod", type=float, default=0.50)
    ap.add_argument("--seed", type=int, default=20261001)
    args = ap.parse_args()

    inp = ROOT / "data" / "raw" / f"{args.instance}.txt"
    out = ROOT / "data" / "derived" / f"{args.instance}_dynamic_dod{int(round(args.dod*100)):03d}_seed{args.seed}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    _, nodes = load_instance(inp)
    depot = nodes[0]

    requests = []

    for p_id, p in nodes.items():
        if p_id == 0 or p["demand"] <= 0:
            continue

        d_id = p["delivery_link"]
        d = nodes[d_id]

        rho_max = p["due"] - dist(depot, p)
        window_width = p["due"] - p["ready"]
        delta = 0.5 * window_width

        requests.append({
            "pickup": p_id,
            "delivery": d_id,
            "q": p["demand"],
            "pickup_ready": p["ready"],
            "pickup_due": p["due"],
            "delivery_ready": d["ready"],
            "delivery_due": d["due"],
            "pickup_service": p["service"],
            "delivery_service": d["service"],
            "rho_max": rho_max,
            "delta": delta,
        })

    random.seed(args.seed)

    n = len(requests)
    n_dynamic = round(args.dod * n)
    dynamic_idx = set(random.sample(range(n), n_dynamic))

    out_rows = []

    for idx, r in enumerate(requests):
        if idx in dynamic_idx:
            upper = max(0.0, r["rho_max"] - r["delta"])
            dynamic = 1
            release = random.uniform(0.0, upper)
        else:
            dynamic = 0
            release = 0.0

        out_rows.append({
            **r,
            "dynamic": dynamic,
            "release_time": release,
            "reaction_margin": r["rho_max"] - release,
        })

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_rows[0].keys())
        writer.writeheader()
        writer.writerows(out_rows)

    dyn = [r for r in out_rows if r["dynamic"]]
    print(f"Saved: {out}")
    print("requests =", n)
    print("static J =", n - len(dyn))
    print("dynamic K =", len(dyn))
    print("realized DoD =", round(len(dyn) / n, 4))
    print("seed =", args.seed)

if __name__ == "__main__":
    main()
