# induced-outerplanar

Computational experiments for induced outerplanar subgraphs in planar triangulations.

This repository contains scripts, logs (CSV), and figures used in our study of the maximum size of an induced outerplanar subgraph in planar triangulations, including adversarial evolutionary search via edge flips.

## What this repo contains

Main scripts:
- evolve_n200_greedyavg_fitness_flip.py
  Evolutionary search on planar triangulations (n=200) guided by greedy-average fitness, with local-search confirmation on bottom candidates.
- make_plot.py
  Plot Figure 1 (greedy fitness evolution) from the summary CSV.
- make_plot2.py
  Plot Figure 2 (min LS-confirm ratio over generations) from the summary CSV.

Experiment outputs (already included):
- evolve_n200_greedyavg_summary.csv
  Per-generation summary statistics for the evolutionary run.
- evolve_n200_greedyavg_bottom.csv
  Bottom-ranked candidates per generation (includes graph6 strings and scores).
- fig1_greedy_fitness_evolution.(png|pdf)
- fig2_ls_confirm_min_over_gens.(png|pdf)

README note:
- If you re-run experiments, file names may change depending on your script settings. The included CSV/PDF/PNG files correspond to one concrete run.

## Requirements

Core requirement:
- SageMath (used for triangulation generation, graph operations, and outerplanarity tests)

Python packages (usually available in Sage’s Python):
- pandas
- matplotlib

If you run scripts via Sage’s Python, you typically do not need a separate venv.

## Quick start

1) Install SageMath
- macOS: install SageMath.app from the official distribution.
- Confirm:
  sage
  sage: 1+1

2) Run an evolutionary experiment (n=200)
This can take time depending on your machine and parameters.

  sage -python evolve_n200_greedyavg_fitness_flip.py

This will generate summary/bottom CSV files (or overwrite them if configured that way in the script).

3) Reproduce figures from CSV

  sage -python make_plot.py
  sage -python make_plot2.py

The scripts output PNG/PDF figures (see files in the repository root).

## Reproducing the main numbers

Multi-size two-stage experiments (n in {40,60,80,100}):
- The repository may include a separate summary CSV (e.g., ratios_multin_twostage_summary.csv) in your local work.
- If you keep it in this repo later, document the script and parameters used to produce it.

Evolutionary experiment (n=200):
- greedy fitness evolution is in evolve_n200_greedyavg_summary.csv (fit_mean, fit_min, survivor_fit_mean)
- LS-confirm minimum over generations is in evolve_n200_greedyavg_summary.csv (ls_confirm_min_bottom20)

## Experiment parameters

### Evolutionary search (n = 200)

| Parameter | Value | Notes |
|---|---:|---|
| n_target | 200 | Number of vertices in triangulations |
| generations | 30 | Total generations; including generation 0 gives 31 snapshots |
| population_size | 320 | Number of triangulations evaluated per generation |
| greedy_runs | 5 | Fitness = average over these randomized greedy runs |
| bottom_k (survivors) | 200 | Selected as worst by fitness (smaller ratio) |
| bottom_check (LS confirm) | 20 | Local search applied only to the worst 20 per generation |
| ls_iters | 20000 | Iterations for local search confirmation |
| flips_per_child | 400 | Edge flips per mutated child |
| children_per_parent | 1 | One child per survivor (mutation-only evolution) |
| extra_random_each_gen | 80 | Fresh random triangulations injected per generation |
| seed | 12345 | Random seed (Python + Sage) |

Derived scale (from the above):
- Triangulations evaluated: 320 × 31 = 9,920
- Greedy runs executed: 9,920 × 5 = 49,600
- Local-search confirmations: 20 × 31 = 620 instances

### Multi-size two-stage experiments (n ∈ {40, 60, 80, 100})

| Parameter | Value | Notes |
|---|---:|---|
| n_list | {40, 60, 80, 100} | Graph sizes tested |
| trials | 1000 | Random triangulations per n |
| greedy_restarts | 10 | Greedy run restarts; best solution among restarts |
| bottom_k | 50 | Only the bottom 50 (worst by greedy ratio) get local search |
| ls_iters | 20000 | Iterations for local search on bottom_k |
| seed | 12345 | Random seed (Python + Sage) |

Derived scale (per n):
- Triangulations evaluated: 1000
- Greedy executions: 1000 × 10 = 10,000
- Local-search applications: 50

Derived scale (total over 4 sizes):
- Triangulations evaluated: 4,000
- Greedy executions: 40,000
- Local-search applications: 200

## Method overview (high-level)

- We generate planar triangulations (initially random).
- We apply edge flips to explore the space of triangulations while preserving triangulation structure.
- For each triangulation G:
  - Greedy heuristic repeatedly removes vertices until the remaining induced subgraph is outerplanar.
  - Fitness is computed from multiple randomized greedy runs (average ratio).
  - Local search is applied only to a small worst-ranked subset for confirmation.

This setup intentionally searches for triangulations that are hard for greedy heuristics, then checks whether local improvement still recovers large induced outerplanar subgraphs.

## Data format notes

- graph6 strings appear in CSV files as a compact, reproducible graph encoding.
- CSV columns are intended to be self-explanatory (generation, ratios, etc.). If you modify the scripts, keep column names stable to avoid breaking plotting scripts.

## Citation

If you use this code or data, please cite:

Kenichi Iwata and Mariko Sasakura,
“On the Size of Induced Outerplanar Subgraphs in Planar Triangulations.”
(preprint in preparation)

(Replace with an arXiv link once available.)

