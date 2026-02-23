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

## License

Add a license file if you plan to accept external contributions or want to clarify reuse.
MIT or BSD-2-Clause are typical choices for research code.