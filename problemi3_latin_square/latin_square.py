import argparse
import math
import random
import sys
import time


SEED = 0  # fixed seed: the shuffled order is the same on every run


class LatinSquareSearch:

    def __init__(self, n):
        self.n = n
        self.grid = [[0] * n for _ in range(n)]
        self.row_used = [0] * n
        self.col_used = [0] * n
        # Reduced form: first row and first column = 1..n (renaming numbers / reordering rows loses no solution)
        for c in range(n):
            self._put(0, c, c + 1)
        for r in range(1, n):
            self._put(r, 0, r + 1)
        self.cells = [(r, c) for r in range(1, n) for c in range(1, n)]
        self.depth = len(self.cells)   # every solution is at depth (n-1)^2
        self.nodes = 0

    def _put(self, r, c, v):
        self.grid[r][c] = v
        self.row_used[r] |= 1 << v
        self.col_used[c] |= 1 << v

    def _remove(self, r, c, v):
        self.grid[r][c] = 0
        self.row_used[r] &= ~(1 << v)
        self.col_used[c] &= ~(1 << v)

    def _candidates(self, k, rng):
        r, c = self.cells[k]
        used = self.row_used[r] | self.col_used[c]
        values = [v for v in range(1, self.n + 1) if not used >> v & 1]   # pruning: not in row or column
        rng.shuffle(values)
        return values

    def _dfs(self, k, limit, rng):
        self.nodes += 1
        if k == self.depth:
            return True
        if limit is not None and k == limit:   # depth limit reached (only used by IDDFS)
            return False
        r, c = self.cells[k]
        for v in self._candidates(k, rng):
            self._put(r, c, v)
            if self._dfs(k + 1, limit, rng):
                return True
            self._remove(r, c, v)              # backtrack
        return False

    def iddfs(self, trace=False):
        iterations = []
        # IDDFS: depth-limited DFS with limit 0, 1, 2, ... until a solution is found
        for limit in range(self.depth + 1):
            before = self.nodes
            found = self._dfs(0, limit, random.Random(SEED))
            iterations.append(self.nodes - before)
            if trace:
                print(f"  limit {limit:>3}: {iterations[-1]:>12,} nodes"
                      + ("  <- solution" if found else ""))
            if found:
                return True, iterations
        return False, iterations

    def backtracking(self):
        return self._dfs(0, None, random.Random(SEED))

    def count(self):
        return self._count(0)   # counts reduced squares; total = n! * (n-1)! * reduced

    def _count(self, k):
        self.nodes += 1
        if k == self.depth:
            return 1
        r, c = self.cells[k]
        used = self.row_used[r] | self.col_used[c]
        total = 0
        for v in range(1, self.n + 1):
            if not used >> v & 1:
                self._put(r, c, v)
                total += self._count(k + 1)
                self._remove(r, c, v)
        return total


def is_latin_square(grid):
    n = len(grid)
    want = list(range(1, n + 1))
    return all(sorted(row) == want for row in grid) and \
        all(sorted(grid[r][c] for r in range(n)) == want for c in range(n))


def main():
    ap = argparse.ArgumentParser(description="Latin Square with IDDFS and Backtracking")
    ap.add_argument("n", type=int, nargs="?", default=5, help="size of the square (default 5)")
    ap.add_argument("--method", choices=["iddfs", "backtracking"], default="iddfs")
    ap.add_argument("--trace", action="store_true", help="print the nodes of every iteration (IDDFS)")
    ap.add_argument("--count", action="store_true",
                    help="count ALL Latin squares of size n (checks correctness against known values)")
    a = ap.parse_args()
    if a.n < 1:
        sys.exit("n must be >= 1")
    sys.setrecursionlimit(max(1000, a.n * a.n + 500))

    s = LatinSquareSearch(a.n)
    t0 = time.perf_counter()
    if a.count:
        try:
            reduced = s.count()
        except KeyboardInterrupt:
            print(f"Stopped by user after {time.perf_counter() - t0:.0f} s ({s.nodes:,} nodes).")
            return
        total = math.factorial(a.n) * math.factorial(a.n - 1) * reduced
        print(f"n = {a.n}")
        print(f"Reduced Latin squares (first row and column = 1..n): {reduced:,}")
        print(f"All Latin squares = n! * (n-1)! * reduced = {total:,}")
        print(f"DFS visited {s.nodes:,} nodes in {time.perf_counter() - t0:.3f} s")
        return
    try:
        if a.method == "iddfs":
            found, iters = s.iddfs(a.trace)
        else:
            found, iters = s.backtracking(), None
    except KeyboardInterrupt:
        print(f"Stopped by user after {time.perf_counter() - t0:.0f} s ({s.nodes:,} nodes). "
              + ("IDDFS spends its time on all levels before depth "
                 f"{s.depth}; try --method backtracking." if a.method == "iddfs" else ""))
        return
    secs = time.perf_counter() - t0

    print(f"Input: {a.n}\nOutput:")
    for row in s.grid:
        print(" ".join(str(v) for v in row))
    print()
    if a.method == "iddfs":
        print(f"IDDFS: solution at depth {s.depth} | {len(iters)} iterations | "
              f"{s.nodes:,} nodes in total, {iters[-1]:,} of them in the last iteration | "
              f"{secs:.3f} s")
    else:
        print(f"Backtracking: {s.nodes:,} nodes | {secs:.3f} s")
    print(f"Check: {'valid Latin square' if is_latin_square(s.grid) else 'NOT VALID'}")


if __name__ == "__main__":
    main()
