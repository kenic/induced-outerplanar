# pick_forest_small_candidates_n30.py
# Run: sage -python pick_forest_small_candidates_n30.py
#
# From exact_verify_n30_results.csv (contains graph6 and exact opout),
# 1) compute a fast heuristic estimate for maximum induced forest size
# 2) pick the most "forest-small" candidates
# 3) run exact min-FVS BB (time-limited) only on those candidates
# 4) output a comparison table: forest_opt (if certified) vs opout_exact

from sage.all import *
import csv, time

IN_CSV = "exact_verify_n30_results.csv"
OUT_CSV = "forest_small_candidates_n30.csv"
OUT_SUM = "forest_small_candidates_n30_summary.txt"

# -------------------------
# Forest test
# -------------------------
def is_forest_fast(H):
    # forest <=> m = n - c
    return H.size() == H.order() - H.connected_components_number()

def strip_leaves(G):
    H = G.copy()
    changed = True
    while changed:
        changed = False
        for v in list(H.vertices()):
            if H.degree(v) <= 1:
                H.delete_vertex(v)
                changed = True
    return H

def find_cycle_vertices(H):
    if is_forest_fast(H):
        return []
    # find a cycle from a non-tree edge in some component
    for comp in H.connected_components():
        if len(comp) <= 2:
            continue
        C = H.subgraph(comp)
        root = comp[0]
        parent = {root: None}
        depth = {root: 0}
        stack = [root]
        tree_edges = set()
        while stack:
            u = stack.pop()
            for v in C.neighbors(u):
                if v not in parent:
                    parent[v] = u
                    depth[v] = depth[u] + 1
                    stack.append(v)
                    tree_edges.add((min(u,v), max(u,v)))
        for (u,v) in C.edges(labels=False):
            e = (min(u,v), max(u,v))
            if e in tree_edges:
                continue
            # recover path u..LCA..v (naive)
            uu, vv = u, v
            path_u = [uu]
            path_v = [vv]
            seen_u = {uu}
            seen_v = {vv}
            while uu != vv:
                if depth[uu] >= depth[vv] and parent[uu] is not None:
                    uu = parent[uu]; path_u.append(uu)
                    if uu in seen_v: break
                    seen_u.add(uu)
                elif parent[vv] is not None:
                    vv = parent[vv]; path_v.append(vv)
                    if vv in seen_u: break
                    seen_v.add(vv)
                else:
                    break
            meet = uu if uu == vv else (uu if uu in seen_v else vv)
            cyc = []
            for x in path_u:
                cyc.append(x)
                if x == meet: break
            tmp = []
            for x in path_v:
                tmp.append(x)
                if x == meet: break
            if tmp:
                tmp.pop()
            cyc.extend(reversed(tmp))
            # unique-preserving
            out = []
            seen = set()
            for x in cyc:
                if x not in seen:
                    out.append(x); seen.add(x)
            return out
    return list(H.vertices())[:3]

def greedy_fvs_heuristic(G):
    """
    Fast heuristic for FVS size:
    repeatedly strip leaves, find a cycle, remove a high-degree vertex on it.
    Returns (fvs_size, removed_set).
    """
    H = strip_leaves(G)
    removed = set()
    while not is_forest_fast(H):
        cyc = find_cycle_vertices(H)
        # pick vertex on cycle with largest degree in current graph
        v = max(cyc, key=lambda x: H.degree(x))
        removed.add(v)
        H.delete_vertex(v)
        H = strip_leaves(H)
    return len(removed), removed

def greedy_triangle_packing_lower_bound(H):
    """
    Lower bound on min FVS using vertex-disjoint triangles.
    Each triangle is a cycle -> must hit at least one vertex in FVS.
    """
    used = set()
    lb = 0
    V = list(H.vertices())
    for u in V:
        if u in used: continue
        Nu = set(H.neighbors(u)) - used
        for v in Nu:
            if v in used or v <= u: continue
            common = (Nu & set(H.neighbors(v))) - used
            for w in common:
                if w in used or w <= v: continue
                used.add(u); used.add(v); used.add(w)
                lb += 1
                break
            if u in used:
                break
    return lb

def min_fvs_bb_fast(G, time_limit_sec=120.0):
    """
    Exact min FVS with reductions + triangle-packing LB.
    Returns (best_fvs, status, elapsed_sec).
    """
    start = time.time()
    # heuristic UB
    ub, _ = greedy_fvs_heuristic(G)
    best = ub

    def dfs(Hcur, removed_count):
        nonlocal best
        if time.time() - start > time_limit_sec:
            return False
        if removed_count >= best:
            return True

        Hred = strip_leaves(Hcur)
        if is_forest_fast(Hred):
            best = min(best, removed_count)
            return True

        lb = greedy_triangle_packing_lower_bound(Hred)
        if removed_count + lb >= best:
            return True

        cyc = find_cycle_vertices(Hred)
        # branch on cycle vertices (high degree first)
        cyc_sorted = sorted(cyc, key=lambda v: Hred.degree(v), reverse=True)
        for v in cyc_sorted:
            Hnext = Hred.copy()
            Hnext.delete_vertex(v)
            finished = dfs(Hnext, removed_count + 1)
            if not finished:
                return False
        return True

    finished = dfs(G, 0)
    status = "OPTIMAL" if finished else "TIMEOUT"
    return best, status, time.time() - start

def main():
    # parameters you can tweak
    pick_K = 30            # how many "forest-small-looking" candidates to exact-check
    exact_time_limit = 120 # seconds per candidate for exact forest (min FVS)

    # load opout CSV
    with open(IN_CSV, "r", newline="") as f:
        rows = list(csv.DictReader(f))

    # compute heuristic forest estimate for all
    scored = []
    t0 = time.time()
    for r in rows:
        g6 = r["graph6"]
        G = Graph(g6)
        n = G.order()

        fvs_h, _ = greedy_fvs_heuristic(G)
        forest_h = n - fvs_h  # heuristic induced-forest size

        scored.append((forest_h, fvs_h, r))

    # pick smallest forest_h
    scored.sort(key=lambda x: x[0])
    candidates = scored[:pick_K]

    # exact-check only candidates
    out = []
    certified = 0
    for rank, (forest_h, fvs_h, r) in enumerate(candidates, start=1):
        g6 = r["graph6"]
        G = Graph(g6)
        n = int(r["n"])
        opout_exact = int(r["exact"])
        opout_status = r["status"]

        fvs_opt, f_st, f_t = min_fvs_bb_fast(G, time_limit_sec=exact_time_limit)
        forest_opt = n - fvs_opt

        if f_st == "OPTIMAL":
            certified += 1

        out.append({
            "rank": rank,
            "idx": int(r["idx"]),
            "n": n,
            "forest_h": forest_h,
            "forest_opt": forest_opt,
            "forest_status": f_st,
            "forest_time": f"{f_t:.3f}",
            "opout_exact": opout_exact,
            "opout_status": opout_status,
            "gap_opout_minus_forest_opt": opout_exact - forest_opt,
            "graph6": g6
        })

        if rank % 5 == 0:
            print(f"[{rank}/{pick_K}] certified={certified} elapsed={time.time()-t0:.1f}s")

    # write CSV
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "rank","idx","n",
            "forest_h","forest_opt","forest_status","forest_time",
            "opout_exact","opout_status",
            "gap_opout_minus_forest_opt",
            "graph6"
        ])
        for d in out:
            w.writerow([
                d["rank"], d["idx"], d["n"],
                d["forest_h"], d["forest_opt"], d["forest_status"], d["forest_time"],
                d["opout_exact"], d["opout_status"],
                d["gap_opout_minus_forest_opt"],
                d["graph6"]
            ])

    # summary
    cert_only = [d for d in out if d["forest_status"] == "OPTIMAL"]
    with open(OUT_SUM, "w") as f:
        f.write(f"input={IN_CSV}\n")
        f.write(f"pick_K={pick_K}\n")
        f.write(f"exact_time_limit_sec={exact_time_limit}\n")
        f.write(f"certified_forest={len(cert_only)}/{pick_K}\n")
        if cert_only:
            mins = min(d["forest_opt"] for d in cert_only)
            f.write(f"min_forest_opt_among_certified={mins}\n")
            max_gap = max(d["gap_opout_minus_forest_opt"] for d in cert_only)
            f.write(f"max_gap_opout_minus_forest_opt_among_certified={max_gap}\n")

    print("DONE")
    print("wrote:", OUT_CSV)
    print("wrote:", OUT_SUM)

if __name__ == "__main__":
    main()
