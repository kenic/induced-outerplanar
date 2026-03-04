# exact_verify_n30_bb.py
# Run: sage -python exact_verify_n30_bb.py
#
# Generates 1000 random planar triangulations with n=40,
# computes heuristic solution size (greedy restarts + local search),
# then attempts to compute the exact optimum via branch-and-bound
# using an outerplanarity oracle (is_circular_planar).
#
# Output:
# - exact_verify_n30_results.csv
# - exact_verify_n30_summary.txt
#
# Notes:
# - Exact solving is exponential in worst case; we use per-instance time limits.
# - Even timeouts are useful: they still provide a certified lower bound.

from sage.all import *
import csv
import time
import random
from statistics import mean, median

# -----------------------------
# Outerplanar oracle
# -----------------------------
def is_outerplanar(H):
    # Sage's outerplanar / circular planar test
    return H.is_circular_planar()

# -----------------------------
# Greedy heuristic (same style as your earlier code)
# -----------------------------
def greedy_outerplanar_induced(G, rng):
    S = set(G.vertices())
    H = G.subgraph(S)

    while not is_outerplanar(H):
        best_score = None
        best_vs = []

        vs = list(S)
        rng.shuffle(vs)

        for v in vs:
            deg = H.degree(v)
            Nv = list(H.neighbors(v))
            Nv_set = set(Nv)

            # edges induced by neighborhood (simple density proxy)
            e_in = 0
            for a in Nv:
                for b in H.neighbors(a):
                    if b in Nv_set and b > a:
                        e_in += 1

            score = 3 * deg + 2 * e_in

            if best_score is None or score > best_score:
                best_score = score
                best_vs = [v]
            elif score == best_score:
                best_vs.append(v)

        vdel = rng.choice(best_vs)
        S.remove(vdel)
        H = G.subgraph(S)

    return S

def greedy_best_of_restarts(G, restarts, seed):
    best = set()
    for r in range(restarts):
        rng = random.Random(seed + 10007 * r)
        S = greedy_outerplanar_induced(G, rng)
        if len(S) > len(best):
            best = set(S)
    return best

# -----------------------------
# Local search (improves a feasible set)
# -----------------------------
def local_search(G, S0, iters, seed):
    rng = random.Random(seed)
    V = list(G.vertices())

    S = set(S0)
    best = set(S)

    def ok(Sset):
        return is_outerplanar(G.subgraph(Sset))

    if not ok(S):
        return best

    for _ in range(iters):
        if rng.random() < 0.4:
            v = rng.choice(V)
            if v not in S:
                S2 = S | {v}
                if ok(S2):
                    S = S2
                    if len(S) > len(best):
                        best = set(S)
        else:
            if not S:
                continue
            v_in = rng.choice(V)
            if v_in in S:
                continue
            v_out = rng.choice(list(S))
            S2 = (S - {v_out}) | {v_in}
            if ok(S2):
                S = S2
                if len(S) > len(best):
                    best = set(S)

    return best

# -----------------------------
# Exact solver: branch-and-bound on vertex inclusion
# Uses hereditary property: induced subgraph of outerplanar is outerplanar.
# We maintain a feasible set S; when trying to include a vertex, check feasibility via oracle.
# -----------------------------
def exact_max_induced_outerplanar_bb(G, initial_lb_set, time_limit_sec=30.0):
    import time
    start = time.time()

    V = list(G.vertices())
    V.sort(key=lambda v: G.degree(v), reverse=True)

    feas_cache = {}
    def ok(Sset):
        key = frozenset(Sset)
        if key in feas_cache:
            return feas_cache[key]
        val = is_outerplanar(G.subgraph(Sset))
        feas_cache[key] = val
        return val

    best_set = set(initial_lb_set) if initial_lb_set is not None else set()
    if best_set and not ok(best_set):
        best_set = set()
    best = len(best_set)

    def dfs(i, S):
        nonlocal best, best_set
        if time.time() - start > time_limit_sec:
            return False

        # trivial upper bound
        if len(S) + (len(V) - i) <= best:
            return True

        if i == len(V):
            if len(S) > best:
                best = len(S)
                best_set = set(S)
            return True

        v = V[i]

        S_inc = S | {v}
        if ok(S_inc):
            finished = dfs(i + 1, S_inc)
            if not finished:
                return False

        finished = dfs(i + 1, S)
        if not finished:
            return False

        return True

    finished = dfs(0, set())
    status = "OPTIMAL" if finished else "TIMEOUT"
    return best, best_set, status, time.time() - start

# -----------------------------
# Main experiment
# -----------------------------
def main():
    # Settings
    n = 30
    trials = 200

    greedy_restarts = 10
    ls_iters = 20000

    # Exact solver budget per instance (seconds)
    # Start with 3 seconds; if too slow, lower to 1-2 sec.
    exact_time_limit = 30.0

    seed = 12345
    random.seed(seed)
    set_random_seed(seed)

    out_csv = "exact_verify_n30_results.csv"
    out_sum = "exact_verify_n30_summary.txt"

    rows = []
    opt_gaps = []
    timeouts = 0

    t0 = time.time()

    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "idx", "n", "m",
            "heur_greedy", "heur_ls",
            "exact", "gap_exact_minus_ls",
            "status", "solve_time_sec",
            "graph6"
        ])

        for i in range(trials):
            # Generate triangulation
            G = graphs.RandomTriangulation(n)

            # Heuristic lower bound: greedy+LS
            Sg = greedy_best_of_restarts(G, greedy_restarts, seed + i * 99991)
            heur_greedy = len(Sg)

            Sls = local_search(G, Sg, ls_iters, seed + i * 77777)
            heur_ls = len(Sls)

            # Exact solve with LB = Sls
            exact_val, exact_set, status, st = exact_max_induced_outerplanar_bb(
                G, Sls, time_limit_sec=exact_time_limit
            )

            gap = exact_val - heur_ls
            if status == "OPTIMAL":
                opt_gaps.append(gap)
            else:
                timeouts += 1

            w.writerow([
                i, n, G.size(),
                heur_greedy, heur_ls,
                exact_val, gap,
                status, f"{st:.4f}",
                G.graph6_string()
            ])

    if (i + 1) % 50 == 0:
        elapsed = time.time() - t0
        if opt_gaps:
            avg_gap = mean(opt_gaps)
            opt_cases = len(opt_gaps)
        else:
            avg_gap = None
            opt_cases = 0
        print(f"[{i+1}/{trials}] elapsed={elapsed:.1f}s timeouts={timeouts} "
              f"optimal_cases={opt_cases} avg_gap_opt={(f'{avg_gap:.3f}' if avg_gap is not None else 'NA')}")

    total_elapsed = time.time() - t0

    with open(out_sum, "w") as f:
        f.write(f"n={n}, trials={trials}\n")
        f.write(f"greedy_restarts={greedy_restarts}, ls_iters={ls_iters}\n")
        f.write(f"exact_time_limit_sec={exact_time_limit}\n")
        f.write(f"total_elapsed_sec={total_elapsed:.2f}\n")
        f.write(f"timeouts={timeouts}\n")
        if opt_gaps:
            f.write(f"optimal_cases={len(opt_gaps)}\n")
            f.write(f"gap_exact_minus_ls: min={min(opt_gaps)}, med={sorted(opt_gaps)[len(opt_gaps)//2]}, mean={mean(opt_gaps):.3f}, max={max(opt_gaps)}\n")
        else:
            f.write("optimal_cases=0\n")

    print("DONE")
    print("results:", out_csv)
    print("summary:", out_sum)

if __name__ == "__main__":
    main()
