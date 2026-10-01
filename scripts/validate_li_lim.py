#!/usr/bin/env python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

FILES = ["lc101.txt", "lr101.txt", "lrc101.txt"]

def load_instance(path):
    lines = [x.strip() for x in path.read_text().splitlines() if x.strip()]
    header = list(map(float, lines[0].split()))
    rows = [list(map(float, x.split())) for x in lines[1:]]

    nodes = {}
    for row in rows:
        i = int(row[0])
        nodes[i] = {
            "x": row[1],
            "y": row[2],
            "demand": row[3],
            "ready": row[4],
            "due": row[5],
            "service": row[6],
            "pickup": int(row[7]),
            "delivery": int(row[8]),
        }
    return header, nodes

failed = False

for fn in FILES:
    path = RAW / fn
    if not path.exists():
        print(f"[MISSING] {path}")
        failed = True
        continue

    header, nodes = load_instance(path)
    pickups = [i for i, n in nodes.items() if i != 0 and n["demand"] > 0]
    deliveries = [i for i, n in nodes.items() if i != 0 and n["demand"] < 0]

    errors = []

    for p in pickups:
        d = nodes[p]["delivery"]

        if d not in nodes:
            errors.append((p, "missing_delivery", d))
            continue

        if nodes[d]["pickup"] != p:
            errors.append((p, "reverse_link_mismatch", d, nodes[d]["pickup"]))

        if abs(nodes[p]["demand"] + nodes[d]["demand"]) > 1e-9:
            errors.append((p, "demand_mismatch", nodes[p]["demand"], nodes[d]["demand"]))

    print(f"\n=== {fn} ===")
    print("header =", header)
    print("nodes excluding depot =", len(nodes) - 1)
    print("pickups =", len(pickups))
    print("deliveries =", len(deliveries))
    print("requests =", len(pickups))
    print("pairing errors =", len(errors))

    if errors:
        failed = True
        for e in errors[:20]:
            print("  ", e)

if failed:
    sys.exit(1)

print("\nValidation OK.")
