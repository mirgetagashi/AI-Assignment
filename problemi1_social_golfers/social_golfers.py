import argparse
import random
import sys
import time
from itertools import combinations


SEED = 0
TIME_LIMIT = 60.0


class Timeout(Exception):
    pass


def solve(g, p, w):
    rng = random.Random(SEED)
    n = g * p
    gp = n
    total = w * gp
    ALL = (1 << n) - 1
    met = [0] * n
    slots = [-1] * total
    nodes = 0
    deadline = time.perf_counter() + TIME_LIMIT
    sys.setrecursionlimit(max(sys.getrecursionlimit(), total + 1000))

    for x in range(n):
        slots[x] = x
    for grp in range(g):
        mask = ((1 << p) - 1) << (grp * p)
        for m in range(grp * p, (grp + 1) * p):
            met[m] |= mask & ~(1 << m)

    def dfs(slot, week_mask, group_mask, forbid, last):
        nonlocal nodes
        nodes += 1
        if nodes & 0xFFF == 0 and time.perf_counter() > deadline:
            raise Timeout
        if slot == total:
            return True

        week, rem = divmod(slot, gp)
        group, pos = divmod(rem, p)
        if pos == 0:
            group_mask = forbid = 0
            last = -1
            if group == 0:
                week_mask = 0
            free = ALL & ~week_mask
            cands = free & -free
        else:
            cands = ALL & ~week_mask & ~forbid
            cands &= ~((1 << (last + 1)) - 1)

        order = []
        while cands:
            low = cands & -cands
            cands ^= low
            order.append(low.bit_length() - 1)
        rng.shuffle(order)

        for x in order:
            low = 1 << x

            slots[slot] = x
            met[x] |= group_mask
            m = group_mask
            while m:
                b = m & -m
                met[b.bit_length() - 1] |= low
                m ^= b

            if dfs(slot + 1, week_mask | low, group_mask | low, forbid | met[x], x):
                return True

            met[x] &= ~group_mask
            m = group_mask
            while m:
                b = m & -m
                met[b.bit_length() - 1] &= ~low
                m ^= b
            slots[slot] = -1
        return False

    try:
        found = dfs(gp, 0, 0, 0, -1)
    except Timeout:
        return None, nodes, "timeout"
    if not found:
        return None, nodes, "infeasible"
    schedule = [[slots[wk * gp + gi * p: wk * gp + (gi + 1) * p] for gi in range(g)]
                for wk in range(w)]
    return schedule, nodes, "solved"


def is_valid(schedule, g, p):
    n = g * p
    seen = set()
    for week in schedule:
        if sorted(x for grp in week for x in grp) != list(range(n)):
            return False
        if any(len(grp) != p for grp in week):
            return False
        for grp in week:
            for pair in combinations(sorted(grp), 2):
                if pair in seen:
                    return False
                seen.add(pair)
    return True


def show(schedule):
    width = len(str(len(schedule[0]) * len(schedule[0][0])))
    for i, week in enumerate(schedule, 1):
        groups = "  ".join("{" + " ".join(str(x + 1).rjust(width) for x in grp) + "}" for grp in week)
        print(f"Week {i:>2}: {groups}")


def main():
    ap = argparse.ArgumentParser(description="Social Golfers Problem with DFS + backtracking")
    ap.add_argument("g", type=int, nargs="?", default=8, help="groups per week (default 8)")
    ap.add_argument("p", type=int, nargs="?", default=4, help="players per group (default 4)")
    ap.add_argument("w", type=int, nargs="?", default=7, help="weeks (default 7)")
    ap.add_argument("--max", action="store_true", help="try w = 1, 2, ... and find the maximum")
    a = ap.parse_args()

    g, p = a.g, a.p
    n = g * p
    bound = (n - 1) // (p - 1)
    print(f"{n} golfers, {g} groups of {p}. Upper bound: (n-1)/(p-1) = {bound} weeks.\n")

    if not a.max:
        t0 = time.perf_counter()
        schedule, nodes, status = solve(g, p, a.w)
        print(f"w = {a.w}: {status}  ({nodes:,} nodes, {time.perf_counter() - t0:.2f} s)\n")
        if schedule:
            show(schedule)
            print(f"\nCheck: {'valid' if is_valid(schedule, g, p) else 'NOT VALID'}")
        return

    best = None
    for w in range(1, bound + 1):
        t0 = time.perf_counter()
        schedule, nodes, status = solve(g, p, w)
        print(f"w = {w:>2}: {status:9} ({nodes:>12,} nodes, {time.perf_counter() - t0:6.2f} s)", flush=True)
        if schedule is None:
            break
        best = schedule
    if best:
        print(f"\nResult: {len(best)} weeks"
              + (" (optimal)" if len(best) == bound or status == "infeasible" else "") + "\n")
        show(best)
        print(f"\nCheck: {'valid' if is_valid(best, g, p) else 'NOT VALID'}")


if __name__ == "__main__":
    main()
