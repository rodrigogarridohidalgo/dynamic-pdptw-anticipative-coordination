#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python}"

echo "== 1. Validate raw benchmark =="
$PYTHON scripts/validate_li_lim.py

echo "== 2. Generate LC101 dynamic instance =="
$PYTHON scripts/generate_dynamic_instance.py \
  --instance lc101 \
  --dod 0.50 \
  --seed 20261001

echo "== 3. Build J->K compatibility =="
$PYTHON scripts/build_transition_graph.py \
  --instance lc101 \
  --dod-tag 050 \
  --seed 20261001

echo "== 4. Build conflict graph =="
$PYTHON scripts/build_conflict_graph.py \
  --instance lc101

echo "== 5. Build economics =="
$PYTHON scripts/build_two_stage_economics.py \
  --instance lc101 \
  --dod-tag 050 \
  --seed 20261001

echo "== 6. Selected joint/sequential experiment =="
$PYTHON scripts/solve_lc101_joint_sequential.py

echo "== 7. Gap decomposition =="
$PYTHON scripts/decompose_lc101_gap.py

echo "== 8. Dense joint/sequential grid =="
$PYTHON scripts/solve_lc101_dense_grid.py

echo "== 9. Dense-grid summary =="
$PYTHON scripts/summarize_lc101_dense.py

echo "== 10. Figures =="
$PYTHON scripts/plot_lc101_regimes.py
$PYTHON scripts/replot_lc101_fleet_interaction.py

echo "== Reproduction completed successfully =="
