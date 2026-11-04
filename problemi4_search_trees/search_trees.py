import argparse
import itertools
import shutil
import subprocess
from collections import deque
from html import escape


class Node:
    def __init__(self, state, parent=None, action=None, status="open", note=""):
        self.state = state
        self.parent = parent
        self.action = action
        self.status = status
        self.note = note
        self.depth = 0 if parent is None else parent.depth + 1
        self.children = []
        self.id = 0
        self.size = 0


# Each problem gives: start state, goal test, and successors(state) -> (action, child, reason if invalid)

class EightPuzzle:
    name = "8-Puzzle"
    algorithm = "BFS"
    MOVES = [("U", -3), ("D", 3), ("L", -1), ("R", 1)]
    NAMES = {"U": "Up", "D": "Down", "L": "Left", "R": "Right"}
    default_depth = 3

    def __init__(self, start=(1, 2, 3, 0, 4, 6, 7, 5, 8), goal=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        self.start, self.goal = start, goal
        self.repeated = "path"        # repeated = same state as an ancestor (e.g. Left then Right)
        self.compact = False

    def is_goal(self, s):
        return s == self.goal

    def successors(self, s):
        b = s.index(0)
        r, c = divmod(b, 3)
        for name, delta in self.MOVES:
            if name == "U" and r == 0 or name == "D" and r == 2 \
                    or name == "L" and c == 0 or name == "R" and c == 2:
                continue
            t = list(s)
            t[b], t[b + delta] = t[b + delta], t[b]
            yield self.NAMES[name], tuple(t), None

    def short(self, action):
        return action

    def text(self, s):
        return " / ".join(" ".join("_" if v == 0 else str(v) for v in s[i:i + 3]) for i in (0, 3, 6))

    def html(self, s, last=None):
        rows = []
        for i in (0, 3, 6):
            cells = "".join(
                f'<TD WIDTH="16" HEIGHT="16" BGCOLOR="{"#d9d9d9" if v == 0 else "white"}">'
                f'<FONT POINT-SIZE="10">{"&nbsp;" if v == 0 else v}</FONT></TD>' for v in s[i:i + 3])
            rows.append(f"<TR>{cells}</TR>")
        return '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">' + "".join(rows) + "</TABLE>"


class MissionariesCannibals:
    name = "Missionaries and Cannibals"
    algorithm = "BFS"
    BOATS = [(1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]
    default_depth = None

    def __init__(self):
        self.start, self.goal = (3, 3, 1), (0, 0, 0)   # (M, C, B) on the left bank
        self.repeated = "global"      # repeated = seen anywhere earlier in the tree
        self.compact = True

    def is_goal(self, s):
        return s == self.goal

    def safe(self, s):
        m, c, _ = s
        return 0 <= m <= 3 and 0 <= c <= 3 and (m == 0 or c <= m) and (m == 3 or 3 - c <= 3 - m)

    def successors(self, s):
        m, c, b = s
        sign = -1 if b == 1 else 1
        for dm, dc in self.BOATS:
            nm, nc = m + sign * dm, c + sign * dc
            label = f"{dm}M {dc}C " + ("→" if b == 1 else "←")
            if not (0 <= nm <= 3 and 0 <= nc <= 3):
                continue
            child = (nm, nc, 1 - b)
            if nm and nc > nm:
                yield label, child, "cannibals > missionaries on the left"
            elif 3 - nm and 3 - nc > 3 - nm:
                yield label, child, "cannibals > missionaries on the right"
            else:
                yield label, child, None

    def short(self, action):
        return "+".join(p for p in action.split()[:2] if not p.startswith("0"))

    def text(self, s):
        m, c, b = s
        return f"({m},{c},{b})"

    def html(self, s, last=None):
        return f"<B>({s[0]},{s[1]},{s[2]})</B>"


class RWS:
    """4 employees share one 28-day cycle: employee e in week w works sequence week (e + w) mod 4."""
    name = "Rotating Workforce Scheduling"
    algorithm = "DFS + backtracking"
    SHIFTS = ["D", "N", "O"]
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    WEEKDAY = {"D": 2, "N": 1, "O": 1}
    WEEKEND = {"D": 1, "N": 1, "O": 2}
    WORK = (3, 5)                   # a block of working days lasts 3..5 days
    REST = (1, 3)                   # a block of days off lasts 1..3 days

    def __init__(self, employees=4):
        self.e = employees
        self.n = employees * 7
        self.demand = [self.WEEKDAY] * 5 + [self.WEEKEND] * 2
        self.start = (None,) * self.n
        self.order = [w * 7 + d for d in range(7) for w in range(self.e)]   # fill day by day
        self.compact = False

    def violation(self, x):
        """Necessary checks on a partial cycle; returns the broken rule or None."""
        n = self.n
        for d in range(7):
            col = [x[w * 7 + d] for w in range(self.e)]
            for s in self.SHIFTS:
                if col.count(s) > self.demand[d][s]:
                    return f"{self.DAY_NAMES[d]} needs {self.demand[d][s]} {s}"
        for i in range(n):
            if x[i] == "N" and x[(i + 1) % n] == "D":
                return "N → D forbidden"
        for i in range(n):
            if x[i] is None or (x[(i - 1) % n] is not None and (x[(i - 1) % n] == "O") == (x[i] == "O")):
                continue
            off, j = x[i] == "O", i
            while x[j % n] is not None and (x[j % n] == "O") == off and j - i < n:
                j += 1
            length, closed = j - i, x[(i - 1) % n] is not None and x[j % n] is not None
            lo, hi = self.REST if off else self.WORK
            kind = "rest" if off else "work"
            if length > hi:
                return f"{kind} block > {hi}"
            if closed and length < lo:
                return f"{kind} block < {lo}"
        return None

    def is_goal(self, s):
        return None not in s and self.violation(s) is None

    def label(self, pos, shift):
        return f"W{pos // 7 + 1} {self.DAY_NAMES[pos % 7]} = {shift}"

    def short(self, action):
        return action

    def text(self, s):
        return " / ".join("".join(v or "?" for v in s[w * 7:(w + 1) * 7]) for w in range(self.e))

    def html(self, s, last=None):
        color = {"D": "#fff2cc", "N": "#cfe2f3", "O": "#eeeeee"}
        head = "<TR><TD></TD>" + "".join(f'<TD><FONT POINT-SIZE="7">{d[:2]}</FONT></TD>'
                                         for d in self.DAY_NAMES) + "</TR>"
        rows = []
        for w in range(self.e):
            cells = ""
            for d in range(7):
                k = w * 7 + d
                v = s[k]
                txt = f"<B>{v}</B>" if k == last else (v or "&nbsp;")
                border = ' COLOR="#1f5fa8"' if k == last else ""
                cells += f'<TD WIDTH="13" HEIGHT="13" BGCOLOR="{color.get(v, "white")}"{border}>' \
                         f'<FONT POINT-SIZE="9">{txt}</FONT></TD>'
            rows.append(f'<TR><TD><FONT POINT-SIZE="7">W{w + 1}</FONT></TD>{cells}</TR>')
        return '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">' + head + "".join(rows) + "</TABLE>"


def build_bfs_tree(problem, max_depth):
    root = Node(problem.start)
    seen = {problem.start}
    queue = deque([root])           # the tree is built with BFS, level by level
    counter = 0
    stats = {"generated": 1, "expanded": 0}
    while queue:
        node = queue.popleft()
        if problem.is_goal(node.state):
            node.status = "goal"
            continue
        if max_depth is not None and node.depth >= max_depth:
            node.status = "frontier"
            continue
        stats["expanded"] += 1
        for action, child_state, invalid in problem.successors(node.state):
            child = Node(child_state, node, action)
            counter += 1
            child.id = counter
            stats["generated"] += 1
            node.children.append(child)
            if invalid:                                   # breaks a constraint: branch is cut
                child.status, child.note = "invalid", invalid
            elif problem.is_goal(child_state):
                child.status = "goal"
            elif problem.repeated == "path" and _on_path(node, child_state):
                child.status = "repeated"                # not expanded, otherwise the tree is infinite
            elif problem.repeated == "global" and child_state in seen:
                child.status = "repeated"
            else:
                seen.add(child_state)
                queue.append(child)
        if not node.children:
            node.status = "frontier"
    nodes = list(walk(root))
    stats["invalid"] = sum(n.status == "invalid" for n in nodes)
    stats["repeated"] = sum(n.status == "repeated" for n in nodes)
    stats["unique states"] = len({n.state for n in nodes})
    return root, stats


def build_dfs_tree(problem):
    """Chronological DFS + backtracking; every tried assignment becomes a node of the tree."""
    stats = {"DFS calls": 0, "tried": 0, "rejected": 0, "backtracked": 0}
    root = Node(problem.start)
    x = list(problem.start)
    counter = [0]

    def dfs(node, k):
        stats["DFS calls"] += 1
        if k == problem.n:                                  # goal test: all positions filled
            node.status = "goal"
            return True
        pos = problem.order[k]
        for shift in problem.SHIFTS:                        # fixed value order, no heuristic
            stats["tried"] += 1
            x[pos] = shift
            counter[0] += 1
            child = Node(tuple(x), node, problem.label(pos, shift))
            child.id, child.note = counter[0], pos
            node.children.append(child)
            reason = problem.violation(x)
            if reason:                                      # pruning: rejected immediately
                stats["rejected"] += 1
                child.status, child.note = "invalid", (pos, reason)
            elif dfs(child, k + 1):
                return True
            else:
                stats["backtracked"] += 1                   # its whole subtree failed
                child.status = "exhausted"
            x[pos] = None
        return False

    dfs(root, 0)
    for n in walk(root):
        n.size = sum(1 for _ in walk(n)) - 1
    return root, stats


def _on_path(node, state):
    while node is not None:
        if node.state == state:
            return True
        node = node.parent
    return False


def walk(node):
    yield node
    for ch in node.children:
        yield from walk(ch)


def goal_paths(root):
    on_path = set()
    for g in (n for n in walk(root) if n.status == "goal"):
        while g is not None:
            on_path.add(g.id)
            g = g.parent
    return on_path


def first_goal(root):
    return next((n for n in walk(root) if n.status == "goal"), None)


def kind(n, on_path):
    if n.status in ("goal", "invalid", "repeated", "exhausted"):
        return n.status
    if n.id in on_path:
        return "path"
    if n.status == "frontier" and not n.children:
        return "frontier"
    if n.children and all(c.status in ("invalid", "repeated") for c in n.children):
        return "dead"
    return "expanded"


# ------------------------------------------------------------------ verification

def verify(problem, root):
    goal = first_goal(root)
    if goal is None:
        return ["no goal in the tree"]
    out = []
    if isinstance(problem, RWS):
        out.append("validator: " + ("PASS" if _validate_rws(problem, goal.state) else "FAIL"))
        other = _independent_rws(problem)
        out.append("independent solver: " + ("same solution" if other == goal.state else "DIFFERENT"))
        return out
    path, n = [], goal
    while n is not None:
        path.append(n.state)
        n = n.parent
    path.reverse()
    legal = all(any(c == b and r is None for _, c, r in problem.successors(a)) for a, b in zip(path, path[1:]))
    out.append("validator: " + ("PASS" if legal and path[0] == problem.start and problem.is_goal(path[-1])
                                else "FAIL"))
    dist = _independent_shortest(problem)
    out.append(f"independent solver: shortest solution = {dist} moves "
               + ("(same depth)" if dist == goal.depth else "(DIFFERENT)"))
    return out


def _independent_shortest(problem):
    dist, queue = {problem.start: 0}, deque([problem.start])
    while queue:
        s = queue.popleft()
        if problem.is_goal(s):
            return dist[s]
        for _, c, bad in problem.successors(s):
            if bad is None and c not in dist:
                dist[c] = dist[s] + 1
                queue.append(c)
    return None


def _validate_rws(p, x):
    rows = [x[w * 7:(w + 1) * 7] for w in range(p.e)]
    for d in range(7):
        col = [rows[w][d] for w in range(p.e)]
        if any(col.count(s) != p.demand[d][s] for s in p.SHIFTS):
            return False
    seq = "".join(x)
    if "ND" in seq + seq[0]:
        return False
    start = next(i for i in range(p.n) if (seq[i] == "O") != (seq[i - 1] == "O"))
    rot = seq[start:] + seq[:start]
    for off, grp in itertools.groupby(rot, key=lambda ch: ch == "O"):
        lo, hi = p.REST if off else p.WORK
        if not lo <= len(list(grp)) <= hi:
            return False
    return True


def _independent_rws(p):
    """Separately written solver: chooses a whole day (column) at a time from its permutations."""
    cols = []
    for d in range(7):
        bag = "".join(s * p.demand[d][s] for s in p.SHIFTS)
        perms = sorted(set(itertools.permutations(bag)), key=lambda t: [p.SHIFTS.index(v) for v in t])
        cols.append(perms)
    grid = [[None] * 7 for _ in range(p.e)]

    def fits():
        seq = [grid[w][d] for w in range(p.e) for d in range(7)]
        for i in range(p.n):
            if seq[i] == "N" and seq[(i + 1) % p.n] == "D":
                return False
        txt = "".join(v or "?" for v in seq)
        for block in txt.replace("?", " ").split():
            for off, grp in itertools.groupby(block, key=lambda ch: ch == "O"):
                if len(list(grp)) > (p.REST if off else p.WORK)[1]:
                    return False
        return True

    def rec(d):
        if d == 7:
            seq = tuple(grid[w][dd] for w in range(p.e) for dd in range(7))
            return seq if _validate_rws(p, seq) else None
        for col in cols[d]:
            for w in range(p.e):
                grid[w][d] = col[w]
            if fits():
                found = rec(d + 1)
                if found:
                    return found
        for w in range(p.e):
            grid[w][d] = None
        return None

    return rec(0)


# ------------------------------------------------------------------ output

TAGS = {"goal": "  ★ GOAL", "invalid": "  ✗ INVALID", "repeated": "  ↺ REPEATED", "frontier": "  …",
        "exhausted": "  ▣ EXHAUSTED", "open": ""}


def visible(root, on_path):
    """Hide what is collapsed: children of exhausted subtrees and of dead ends."""
    hidden = set()
    for n in walk(root):
        if n.parent is not None and (n.parent.id in hidden
                                     or kind(n.parent, on_path) in ("exhausted", "dead")):
            hidden.add(n.id)
    return [n for n in walk(root) if n.id not in hidden]


def print_tree(problem, root):
    on_path = goal_paths(root)
    shown = {n.id for n in visible(root, on_path)}

    def rec(node, prefix, last):
        branch = "" if node.parent is None else ("└── " if last else "├── ")
        act = f"[{node.action}] " if node.action else ""
        note = node.note[1] if node.status == "invalid" and isinstance(node.note, tuple) else node.note
        extra = f" ({note})" if node.status == "invalid" and note else ""
        if node.status == "exhausted":
            extra = f" ({node.size} nodes below)"
        print(f"{prefix}{branch}#{node.id} {act}{problem.text(node.state)}{TAGS.get(node.status, '')}{extra}")
        ext = "" if node.parent is None else ("    " if last else "│   ")
        kids = [c for c in node.children if c.id in shown]
        for i, ch in enumerate(kids):
            rec(ch, prefix + ext, i == len(kids) - 1)
    rec(root, "", True)


STYLE = {   # fill, border, line style, text colour
    "path":      ("#e8f1fb", "#1f5fa8", "solid", "#16467d"),
    "goal":      ("#eaf4e0", "#3b6e1e", "solid,bold", "#2d5517"),
    "invalid":   ("#fbe9e9", "#a33a3a", "solid", "#7a2020"),
    "repeated":  ("#f1efea", "#9a958c", "dashed", "#6b665e"),
    "exhausted": ("#e9e9e9", "#777777", "solid", "#555555"),
    "dead":      ("#fbefdc", "#8a5a1a", "solid", "#6b4210"),
    "expanded":  ("#ffffff", "#555555", "solid", "#333333"),
    "frontier":  ("#ffffff", "#aaaaaa", "dotted", "#777777"),
}
LEGEND = {"path": "Solution path", "goal": "Goal", "invalid": "Invalid ×", "repeated": "Repeated ↺",
          "exhausted": "Exhausted subtree", "dead": "Dead end", "expanded": "Expanded",
          "frontier": "Not expanded (depth limit)"}


def to_dot(problem, root, stats):
    on_path = goal_paths(root)
    nodes = visible(root, on_path)
    max_d = max(n.depth for n in nodes)
    info = " · ".join(f"{k} {v:,}" for k, v in stats.items())
    L = ['digraph tree {',
         '  graph [rankdir=TB, nodesep=0.3, ranksep=0.5, fontname="Helvetica", ordering=out, labelloc=t,',
         f'         fontsize=18, label=<<B>{escape(problem.algorithm)} search tree: {escape(problem.name)}</B><BR/>'
         f'<FONT POINT-SIZE="11" COLOR="#666666">{escape(info)}</FONT><BR/> >];',
         '  node [shape=box, style="rounded,filled", fontname="Helvetica", margin="0.08,0.05"];',
         '  edge [arrowhead=none, color="#b8b4ac", penwidth=1.1];']
    for d in range(max_d + 1):
        L.append(f'  d{d} [label="d={d}", shape=plaintext, style="", fontcolor="#888888", fontsize=11];')
    L.append("  " + " -> ".join(f"d{d}" for d in range(max_d + 1)) + " [style=invis];")
    used = set()
    for n in nodes:
        k = kind(n, on_path)
        used.add(k)
        fill, border, line, text = STYLE[k]
        last = n.note[0] if isinstance(n.note, tuple) else (n.note if isinstance(n.note, int) else None)
        sub = "start" if n.parent is None else problem.short(n.action)
        if k == "invalid":
            reason = n.note[1] if isinstance(n.note, tuple) else n.note
            sub += " ×" + (f"<BR/>{escape(reason)}" if reason and not problem.compact else "")
        elif k == "repeated":
            sub += " ↺"
        elif k == "exhausted":
            sub += f"<BR/>exhausted: {n.size:,} nodes"
        elif k == "goal":
            sub += "<BR/><B>GOAL</B>"
        sub = sub if "<BR/>" in sub else escape(sub)
        if problem.compact:
            body = f'<FONT POINT-SIZE="13" COLOR="{text}">{problem.html(n.state)}</FONT>'
        else:
            body = problem.html(n.state, last)
        lbl = (f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1"><TR><TD>{body}</TD></TR>'
               f'<TR><TD><FONT POINT-SIZE="9" COLOR="{text}">{sub}</FONT></TD></TR></TABLE>>')
        L.append(f'  n{n.id} [label={lbl}, fillcolor="{fill}", color="{border}", style="rounded,filled,{line}"];')
        if n.parent is not None:
            pen = ' [color="#1f5fa8", penwidth=2.4]' if n.id in on_path else ""
            L.append(f"  n{n.parent.id} -> n{n.id}{pen};")
    for d in range(max_d + 1):
        same = " ".join(f"n{n.id};" for n in nodes if n.depth == d)
        L.append(f"  {{rank=same; d{d}; {same}}}")
    cells = ""
    for k in LEGEND:
        if k in used:
            fill, border, _, _ = STYLE[k]
            cells += (f'<TD WIDTH="16" HEIGHT="16" BGCOLOR="{fill}" COLOR="{border}" BORDER="1"> </TD>'
                      f'<TD ALIGN="LEFT">  {escape(LEGEND[k])}      </TD>')
    L.append(f'  legend [shape=plaintext, style="", fontsize=11, label=<<TABLE BORDER="0" CELLSPACING="2">'
             f'<TR>{cells}</TR></TABLE>>];')
    L.append(f"  d{max_d} -> legend [style=invis];")
    L.append("}")
    return "\n".join(L)


def build(problem, depth):
    if isinstance(problem, RWS):
        root, stats = build_dfs_tree(problem)
    else:
        root, stats = build_bfs_tree(problem, depth if depth is not None else problem.default_depth)
    goal = first_goal(root)
    if goal:
        stats["solution depth"] = goal.depth
    return root, stats


def main():
    ap = argparse.ArgumentParser(description="Search trees for 8-Puzzle, M&C and RWS")
    ap.add_argument("problem", choices=["8puzzle", "mc", "rws"])
    ap.add_argument("--depth", type=int, help="maximum depth of the BFS tree (8-Puzzle, M&C)")
    ap.add_argument("--dot", action="store_true", help="print the tree in Graphviz DOT format")
    ap.add_argument("--pdf", metavar="FILE", help="draw the tree into a PDF file (needs Graphviz)")
    a = ap.parse_args()

    problem = {"8puzzle": EightPuzzle, "mc": MissionariesCannibals, "rws": RWS}[a.problem]()
    root, stats = build(problem, a.depth)
    if a.dot:
        print(to_dot(problem, root, stats))
        return
    if a.pdf:
        if shutil.which("dot") is None:
            raise SystemExit("Graphviz is not installed (macOS: brew install graphviz)")
        subprocess.run(["dot", "-Tpdf", "-o", a.pdf], input=to_dot(problem, root, stats), text=True, check=True)
        print(f"Tree written to {a.pdf}")
        return
    print_tree(problem, root)
    print(f"\n{problem.name} ({problem.algorithm}): " + " | ".join(f"{k} {v:,}" for k, v in stats.items()))
    goal = first_goal(root)
    if goal and not isinstance(problem, RWS):
        path, n = [], goal
        while n.parent is not None:
            path.append(n.action)
            n = n.parent
        sep = ", " if any("→" in p or "←" in p for p in path) else " → "
        print("Path to the solution: " + sep.join(reversed(path)))
    if goal and isinstance(problem, RWS):
        print("Solution (one 28-day cycle, rows = consecutive weeks):")
        for w in range(problem.e):
            print(f"  W{w + 1}: " + " ".join(goal.state[w * 7:(w + 1) * 7]))
    for line in verify(problem, root):
        print("Check, " + line)


if __name__ == "__main__":
    main()
