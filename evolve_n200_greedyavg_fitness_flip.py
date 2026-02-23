from sage.all import *
import csv
import time
import random
from statistics import mean

# -----------------------------
# Outerplanar oracle
# -----------------------------
def is_outerplanar(H):
    return H.is_circular_planar()

# -----------------------------
# Greedy induced outerplanar (randomized tie-break)
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

def greedy_once(G, seed):
    rng = random.Random(seed)
    S = greedy_outerplanar_induced(G, rng)
    return len(S)

def greedy_avg_fitness(G, runs, seed):
    # fitness = average ratio over 'runs' randomized greedy executions
    nn = G.order()
    vals = []
    for r in range(runs):
        best = greedy_once(G, seed + 10007 * r)
        vals.append(best / nn)
    return mean(vals)

def greedy_best_solution_for_ls(G, runs, seed):
    # for LS confirmation: start from the best among the same greedy runs
    nn = G.order()
    bestS = None
    bestSize = -1
    for r in range(runs):
        rng = random.Random(seed + 10007 * r)
        S = greedy_outerplanar_induced(G, rng)
        if len(S) > bestSize:
            bestSize = len(S)
            bestS = set(S)
    return bestS, bestSize / nn

# -----------------------------
# Local search (confirm only)
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
# Triangulation edge flip (combinatorial)
# -----------------------------
def random_edge_flip(G, rng, max_tries=300):
    H = G.copy(immutable=False)
    edges = list(H.edges(labels=False))
    if not edges:
        return H, False

    for _ in range(max_tries):
        u, v = rng.choice(edges)

        cn = set(H.neighbors(u)).intersection(H.neighbors(v))
        if len(cn) != 2:
            continue
        a, b = tuple(cn)

        if H.has_edge(a, b):
            continue
        if not H.has_edge(u, v):
            continue

        H.delete_edge(u, v)
        H.add_edge(a, b)
        return H, True

    return H, False

def mutate_by_flips(G, flips, seed):
    rng = random.Random(seed)
    H = G
    done = 0
    for _ in range(flips):
        H2, ok = random_edge_flip(H, rng)
        H = H2
        if ok:
            done += 1
    return H, done

# -----------------------------
# Evaluate population: fitness=avg greedy ratio
# Also keep a best greedy solution (for LS confirmation only)
# -----------------------------
def evaluate_population(pop, n_target, greedy_runs, base_seed):
    recs = []
    for i, G in enumerate(pop):
        nn = G.order()
        mm = G.size()

        fit = greedy_avg_fitness(G, greedy_runs, base_seed + (n_target * 10**6) + i * 99991)

        # store also one "best greedy" solution for later LS check (only needed for bottom20)
        recs.append({
            "idx": i,
            "n": nn,
            "m": mm,
            "fitness": fit,              # avg greedy ratio
            "graph6": G.graph6_string()
        })
    return recs

# -----------------------------
# Evolution loop (fitness = avg greedy ratio; smaller is worse)
# -----------------------------
def evolve():
    n_target = 200
    bottom_k = 200
    bottom_check = 20
    generations = 30

    population_size = 320
    greedy_runs = 5   # A: average over multiple greedy runs

    ls_iters = 20000

    flips_per_child = 400
    children_per_parent = 1
    extra_random_each_gen = 80

    seed = 12345
    random.seed(seed)
    set_random_seed(seed)

    out_summary = f"evolve_n{n_target}_greedyavg_summary.csv"
    out_bottom = f"evolve_n{n_target}_greedyavg_bottom.csv"

    # init population
    pop = []
    for i in range(population_size):
        G = graphs.RandomTriangulation(n_target)
        G2, _ = mutate_by_flips(G, flips=30, seed=seed + i * 101)
        pop.append(G2)

    t_global = time.time()

    with open(out_summary, "w", newline="") as fs, open(out_bottom, "w", newline="") as fb:
        ws = csv.writer(fs)
        wb = csv.writer(fb)

        ws.writerow([
            "gen",
            "pop_size",
            "greedy_runs",
            "bottom_k",
            "flips_per_child",
            "extra_random_each_gen",
            "fit_min", "fit_med", "fit_mean",
            "survivor_fit_min", "survivor_fit_mean",
            "ls_confirm_min_bottom20", "ls_confirm_mean_bottom20",
            "elapsed_s"
        ])

        wb.writerow([
            "gen",
            "rank_by_fitness",
            "n", "m",
            "fitness_avg_greedy_ratio",
            "best_greedy_ratio_for_ls_start",
            "ls_best", "ls_ratio",
            "graph6"
        ])

        for gen in range(generations + 1):
            t0 = time.time()

            recs = evaluate_population(
                pop=pop,
                n_target=n_target,
                greedy_runs=greedy_runs,
                base_seed=seed + gen * 999999
            )

            fits = [r["fitness"] for r in recs]
            fits_sorted = sorted(fits)
            fit_min = fits_sorted[0]
            fit_med = fits_sorted[len(fits_sorted)//2]
            fit_mean = mean(fits)

            # survivors: bottom_k by fitness (smaller is worse)
            recs.sort(key=lambda r: r["fitness"])
            survivors = recs[:bottom_k]
            survivor_fit_min = survivors[0]["fitness"]
            survivor_fit_mean = mean([r["fitness"] for r in survivors])

            # LS confirm only for bottom_check among survivors
            ls_ratios = []
            for rank, r in enumerate(survivors[:bottom_check], start=1):
                G = Graph(r["graph6"])
                nn = G.order()
                mm = G.size()

                # LS start: best greedy among the same 'greedy_runs'
                Sbest, best_g_ratio = greedy_best_solution_for_ls(
                    G, greedy_runs, seed + (n_target*10**6) + gen*10000 + rank*88888
                )

                Sls = local_search(
                    G, Sbest, ls_iters, seed + (n_target*10**6) + gen*10000 + rank*77777
                )
                ls_best = len(Sls)
                ls_ratio = ls_best / nn
                ls_ratios.append(ls_ratio)

                wb.writerow([
                    gen,
                    rank,
                    nn, mm,
                    f"{r['fitness']:.12f}",
                    f"{best_g_ratio:.12f}",
                    ls_best, f"{ls_ratio:.12f}",
                    r["graph6"]
                ])

            ls_min = min(ls_ratios) if ls_ratios else None
            ls_mean20 = mean(ls_ratios) if ls_ratios else None

            elapsed = time.time() - t0

            ws.writerow([
                gen,
                len(pop),
                greedy_runs,
                bottom_k,
                flips_per_child,
                extra_random_each_gen,
                f"{fit_min:.12f}", f"{fit_med:.12f}", f"{fit_mean:.12f}",
                f"{survivor_fit_min:.12f}", f"{survivor_fit_mean:.12f}",
                "" if ls_min is None else f"{ls_min:.12f}",
                "" if ls_mean20 is None else f"{ls_mean20:.12f}",
                f"{elapsed:.2f}"
            ])

            print(f"[gen {gen}] pop={len(pop)} "
                  f"fit(min/med/mean)=({fit_min:.4f}/{fit_med:.4f}/{fit_mean:.4f}) "
                  f"survivor_fit_min={survivor_fit_min:.4f} "
                  f"LS_confirm_min={('%.4f' % ls_min) if ls_min is not None else 'NA'} "
                  f"elapsed={elapsed:.1f}s")

            if gen == generations:
                break

            # next generation
            next_pop = []

            # keep survivors
            for r in survivors:
                next_pop.append(Graph(r["graph6"]))

            # children via flips
            child_target = bottom_k * children_per_parent
            flips_done_list = []
            for i in range(child_target):
                parent = survivors[i % bottom_k]
                Gp = Graph(parent["graph6"])
                Gc, flips_done = mutate_by_flips(
                    Gp,
                    flips=flips_per_child,
                    seed=seed + gen * 100000 + i * 17
                )
                next_pop.append(Gc)
                flips_done_list.append(flips_done)

            # inject fresh random
            for i in range(extra_random_each_gen):
                Gnew = graphs.RandomTriangulation(n_target)
                Gnew2, _ = mutate_by_flips(Gnew, flips=30, seed=seed + gen * 33333 + i)
                next_pop.append(Gnew2)

            # shuffle and trim
            rnd = random.Random(seed + gen * 424242)
            rnd.shuffle(next_pop)
            pop = next_pop[:population_size]

            if flips_done_list:
                print(f"[gen {gen}] avg_flips_done_per_child={mean(flips_done_list):.2f}")

    print("DONE")
    print("summary:", out_summary)
    print("bottom20:", out_bottom)
    print("total_elapsed_s:", time.time() - t_global)

if __name__ == "__main__":
    evolve()
