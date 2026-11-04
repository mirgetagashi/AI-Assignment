import argparse
import os
import sys
import time
from collections import deque

PUZZLES = [
    ("easy-1",      "easy",   "15.3.74....91.4352.3.5.8.6..4..3287..9.4..1....7......9.8..6.4.4.2..3.15.....19.7"),
    ("easy-2",      "easy",   ".3.1972462.....3..96...2.57...6.8.32....4..656539..4.8.49..6..1.263.....5...7...."),
    ("easy-3",      "easy",   ".7.2..9.1...4.....821.6...36.81473...42.3.81519....47638...42.......2..8.1....56."),
    ("euler-01",    "easy",   "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3.."),
    ("medium-1",    "medium", ".5...7.....91.4352.3...8.6..4...287....4..1....7......9.8..6.4.4.2..3..5.....19.7"),
    ("medium-2",    "medium", "2..73.164....6187......82..4.38.7.....6.....9..1......53.1.6.8..1..7..5.7....46.."),
    ("medium-3",    "medium", ".7.2..9.....4.....821.6...36.81473....2.3.8.519.....763.....2.......2..8.1....56."),
    ("euler-02",    "medium", "2...8.3...6..7..84.3.5..2.9...1.54.8.........4.27.6...3.1..7.4.72..4..6...4.1...3"),
    ("hard-1",      "hard",   "......3...1.5.82.98..2.....14......8..79.......8.....3.6.1......3...4.6...56.27.1"),
    ("hard-2",      "hard",   ".3.19.2..2.........6...2.57...6.8.32....4..65.539..4...49..6......3.....5........"),
    ("hard-3",      "hard",   "..7.2..6.12.45....5.........7.....8.2...9...48.....69...3.15..79....3..8.81......"),
    ("inkala-2012", "hard",   "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."),
]

ROWS = [[r * 9 + c for c in range(9)] for r in range(9)]
COLS = [[r * 9 + c for r in range(9)] for c in range(9)]
BOXES = [[(br * 3 + r) * 9 + bc * 3 + c for r in range(3) for c in range(3)]
         for br in range(3) for bc in range(3)]
ROW_OF = [i // 9 for i in range(81)]
COL_OF = [i % 9 for i in range(81)]
BOX_OF = [(i // 27) * 3 + (i % 9) // 3 for i in range(81)]
UNITS = ROWS + COLS + BOXES


def parse(text):
    chars = [ch for ch in text if ch in "123456789.0"]
    if len(chars) != 81:
        raise ValueError(f"81 cells required, found {len(chars)}")
    return bytes(0 if ch in ".0" else int(ch) for ch in chars)


def find_conflicts(puzzle):
    names = [f"row {k + 1}" for k in range(9)] + [f"column {k + 1}" for k in range(9)] \
        + [f"box {k + 1}" for k in range(9)]
    conflicts = []
    for name, unit in zip(names, UNITS):
        digits = [puzzle[i] for i in unit if puzzle[i]]
        for d in sorted(set(digits)):
            if digits.count(d) > 1:
                conflicts.append(f"{name} has digit {d} {digits.count(d)} times")
    return conflicts


def is_valid_solution(grid, puzzle):
    if 0 in grid or any(p and p != s for p, s in zip(puzzle, grid)):
        return False
    return all(sorted(grid[i] for i in unit) == list(range(1, 10)) for unit in UNITS)


def bfs(puzzle):
    stats = {"expanded": 0, "max_queue": 1, "dead_ends": 0}
    queue = deque([puzzle])                      # FIFO queue -> breadth-first
    t0 = time.perf_counter()
    while queue:
        state = queue.popleft()                  # always expand the oldest state first
        stats["expanded"] += 1
        cell = state.index(0)                    # first empty cell in reading order (no MRV)

        used = set()
        for i in ROWS[ROW_OF[cell]]:
            used.add(state[i])
        for i in COLS[COL_OF[cell]]:
            used.add(state[i])
        for i in BOXES[BOX_OF[cell]]:
            used.add(state[i])
        # Pruning (the backtracking part of BFS): only digits that no peer already has
        digits = [d for d in range(1, 10) if d not in used]

        if not digits:                           # dead end: this branch is cut
            stats["dead_ends"] += 1
            continue
        for d in digits:
            child = state[:cell] + bytes((d,)) + state[cell + 1:]
            if 0 not in child:                   # goal test as soon as the child is created
                stats["seconds"] = time.perf_counter() - t0
                return child, stats
            queue.append(child)
        if len(queue) > stats["max_queue"]:
            stats["max_queue"] = len(queue)
    stats["seconds"] = time.perf_counter() - t0
    return None, stats


def side_by_side(puzzle, solution):
    def lines(grid):
        out = ["+-------+-------+-------+"]
        for r in range(9):
            row = grid[r * 9:(r + 1) * 9]
            cells = ["." if v == 0 else str(v) for v in row]
            out.append("| " + " | ".join(" ".join(cells[b * 3:(b + 1) * 3]) for b in range(3)) + " |")
            if r % 3 == 2:
                out.append("+-------+-------+-------+")
        return out
    left, right = lines(puzzle), lines(solution) if solution else [""] * 13
    return "\n".join(f"{a}    {b}" for a, b in zip(left, right))


def run(name, level, puzzle):
    conflicts = find_conflicts(puzzle)
    if conflicts:
        print(f"{name} ({level}, {puzzle.count(0)} empty cells)")
        print(side_by_side(puzzle, None))
        print("Invalid puzzle, not searched: " + "; ".join(conflicts) + "\n")
        return False
    solution, st = bfs(puzzle)
    mb = st["max_queue"] * (sys.getsizeof(puzzle) + 8) / 1e6
    print(f"{name} ({level}, {puzzle.count(0)} empty cells)")
    print(side_by_side(puzzle, solution))
    if solution:
        ok = is_valid_solution(solution, puzzle)
        print(f"BFS: solved in {st['seconds']:.2f} s | {st['expanded']:,} states expanded | "
              f"max queue {st['max_queue']:,} states (~{mb:.1f} MB) | check: {'valid' if ok else 'NOT VALID'}\n")
    else:
        print(f"BFS: no solution exists (the whole tree was searched, {st['expanded']:,} states)\n")
    return solution is not None


def main():
    ap = argparse.ArgumentParser(description="Sudoku with BFS + backtracking")
    ap.add_argument("puzzle", nargs="?", help="81 characters or a path to a file; without it: all puzzles")
    ap.add_argument("--level", choices=["easy", "medium", "hard"])
    a = ap.parse_args()

    if a.puzzle:
        text = open(a.puzzle).read() if os.path.exists(a.puzzle) else a.puzzle
        run("puzzle", "?", parse(text))
        return
    solved = total = 0
    for name, level, text in PUZZLES:
        if a.level and level != a.level:
            continue
        total += 1
        solved += run(name, level, parse(text))
    print(f"Result: {solved}/{total} puzzles solved.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
