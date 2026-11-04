import argparse
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


class EightPuzzle:
    name = "8-Puzzle"
    MOVES = [("U", -3), ("D", 3), ("L", -1), ("R", 1)]
    NAMES = {"U": "Up", "D": "Down", "L": "Left", "R": "Right"}

    def __init__(self, start=(1, 2, 3, 0, 4, 6, 7, 5, 8), goal=(1, 2, 3, 4, 5, 6, 7, 8, 0)):
        self.start, self.goal = start, goal
        self.repeated = "path"

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

    def text(self, s):
        return " / ".join(" ".join("_" if v == 0 else str(v) for v in s[i:i + 3]) for i in (0, 3, 6))

    def html(self, s):
        rows = []
        for i in (0, 3, 6):
            cells = "".join(
                f'<TD WIDTH="18" HEIGHT="18" BGCOLOR="{"#d9d9d9" if v == 0 else "white"}">'
                f'{"&nbsp;" if v == 0 else v}</TD>' for v in s[i:i + 3])
            rows.append(f"<TR>{cells}</TR>")
        return '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">' + "".join(rows) + "</TABLE>"


class MissionariesCannibals:
    name = "Missionaries and Cannibals"
    BOATS = [(1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]

    def __init__(self):
        self.start, self.goal = (3, 3, 1), (0, 0, 0)
        self.repeated = "global"
        self.compact = True

    def is_goal(self, s):
        return s == self.goal

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

    def text(self, s):
        m, c, b = s
        return f"({m},{c},{b})"

    def html(self, s):
        return f"<B>({s[0]},{s[1]},{s[2]})</B>"


class RWS:
    name = "Rotating Workforce Scheduling"
    SHIFTS = ["D", "N", "-"]

    def __init__(self, employees=3, days=7, branch_day2=("D", "N", "-")):
        self.e, self.d = employees, days
        self.start = ()
        self.repeated = "none"
        self.branch_day2 = branch_day2

    def is_goal(self, s):
        return len(s) == self.e * self.d

    def successors(self, s):
        k = len(s)
        day, emp = divmod(k, self.e)
        if day >= 1 and tuple(s[:self.e]) != self.branch_day2:
            return
        today = s[day * self.e:]
        for sh in self.SHIFTS:
            child = s + (sh,)
            if sh == "D" and today.count("D") >= 1:
                yield sh, child, "the day already has 1 D"
            elif sh == "N" and today.count("N") >= 1:
                yield sh, child, "the day already has 1 N"
            elif sh == "-" and today.count("-") >= 1:
                yield sh, child, "someone has to work"
            elif day >= 1 and sh == "D" and s[(day - 1) * self.e + emp] == "N":
                yield sh, child, "N → D forbidden"
            else:
                yield sh, child, None

    def label_action(self, s, action):
        k = len(s)
        day, emp = divmod(k, self.e)
        return f"P{emp + 1} day {day + 1} = {action}"

    def text(self, s):
        if not s:
            return "[empty]"
        cols = [s[i:i + self.e] for i in range(0, len(s), self.e)]
        return " | ".join("".join(col) for col in cols)

    def html(self, s):
        if not s:
            return "<B>empty schedule</B>"
        days = (len(s) + self.e - 1) // self.e
        head = "<TR><TD></TD>" + "".join(f'<TD><FONT POINT-SIZE="8">D{d + 1}</FONT></TD>'
                                         for d in range(days)) + "</TR>"
        rows = []
        for emp in range(self.e):
            cells = ""
            for d in range(days):
                k = d * self.e + emp
                v = s[k] if k < len(s) else "&nbsp;"
                color = {"D": "#fff2cc", "N": "#cfe2f3", "-": "#eeeeee"}.get(v, "white")
                cells += f'<TD WIDTH="16" BGCOLOR="{color}">{v}</TD>'
            rows.append(f'<TR><TD><FONT POINT-SIZE="8">P{emp + 1}</FONT></TD>{cells}</TR>')
        return '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">' + head + "".join(rows) + "</TABLE>"


def build_tree(problem, max_depth):
    root = Node(problem.start)
    seen = {problem.start}
    queue = deque([root])
    counter = 0
    root.id = counter
    while queue:
        node = queue.popleft()
        if problem.is_goal(node.state):
            node.status = "goal"
            continue
        if node.depth >= max_depth:
            node.status = "frontier"
            continue
        for action, child_state, invalid in problem.successors(node.state):
            if hasattr(problem, "label_action"):
                action = problem.label_action(node.state, action)
            child = Node(child_state, node, action)
            counter += 1
            child.id = counter
            node.children.append(child)
            if invalid:
                child.status, child.note = "invalid", invalid
            elif problem.is_goal(child_state):
                child.status = "goal"
            elif problem.repeated == "path" and _on_path(node, child_state):
                child.status = "repeated"
            elif problem.repeated == "global" and child_state in seen:
                child.status = "repeated"
            else:
                seen.add(child_state)
                queue.append(child)
        if not node.children:
            node.status = "frontier"
    return root


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


def solution_path(root):
    goal = next((n for n in walk(root) if n.status == "goal"), None)
    path = set()
    while goal is not None:
        path.add(goal.id)
        goal = goal.parent
    return path


TAGS = {"goal": "  ★ GOAL", "invalid": "  ✗ INVALID", "repeated": "  ↺ REPEATED",
        "frontier": "  …", "open": ""}


def print_tree(problem, root):
    def rec(node, prefix, last):
        branch = "" if node.parent is None else ("└── " if last else "├── ")
        act = f"[{node.action}] " if node.action else ""
        note = f" ({node.note})" if node.note else ""
        print(f"{prefix}{branch}#{node.id} {act}{problem.text(node.state)}{TAGS[node.status]}{note}")
        ext = "" if node.parent is None else ("    " if last else "│   ")
        for i, ch in enumerate(node.children):
            rec(ch, prefix + ext, i == len(node.children) - 1)
    rec(root, "", True)


def to_dot(problem, root):
    on_path = solution_path(root)
    style = {"goal": ("#d9ead3", "#38761d", "bold"), "invalid": ("#f4cccc", "#cc0000", "dashed"),
             "repeated": ("#fff2cc", "#bf9000", "dashed"), "frontier": ("white", "#999999", "dotted"),
             "open": ("white", "#444444", "solid")}
    lines = ["digraph tree {", '  graph [rankdir=TB, nodesep=0.15, ranksep=0.45, fontname="Helvetica"];',
             '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, margin="0.06,0.04"];',
             '  edge [fontname="Helvetica", fontsize=9, color="#666666"];']
    for n in walk(root):
        fill, color, line = style[n.status]
        if n.id in on_path and n.status != "goal":
            color, line = "#38761d", "bold"
        compact = getattr(problem, "compact", False)
        if compact and n.status in ("invalid", "repeated"):
            tag = {"invalid": "<FONT COLOR='#cc0000'>✗</FONT>",
                   "repeated": "<FONT COLOR='#bf9000'>↺</FONT>"}[n.status]
        else:
            tag = None
        tag = tag or {"goal": "<B>★ GOAL</B>",
               "invalid": f"<FONT COLOR='#cc0000' POINT-SIZE='8'>✗ {escape(n.note)}</FONT>",
               "repeated": "<FONT COLOR='#bf9000' POINT-SIZE='8'>↺ repeated</FONT>",
               "frontier": "", "open": ""}[n.status]
        tag_row = f"<TR><TD>{tag}</TD></TR>" if tag else ""
        if compact and n.status in ("invalid", "repeated"):
            label = f"<{problem.html(n.state)} {tag}>"
        else:
            label = (f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">'
                     f'<TR><TD><FONT POINT-SIZE="8" COLOR="#777777">#{n.id}</FONT></TD></TR>'
                     f'<TR><TD>{problem.html(n.state)}</TD></TR>{tag_row}</TABLE>>')
        lines.append(f'  n{n.id} [label={label}, fillcolor="{fill}", color="{color}", style="rounded,filled,{line}"];')
        if n.parent is not None:
            pen = ', color="#38761d", penwidth=2.2' if n.id in on_path else ""
            lines.append(f'  n{n.parent.id} -> n{n.id} [label="{n.action}"{pen}];')
    lines.append("}")
    return "\n".join(lines)


def to_dot_simple(problem, root):
    goals = [n for n in walk(root) if n.status == "goal"]
    on_path = set()
    for g in goals:
        while g is not None:
            on_path.add(g.id)
            g = g.parent

    def kind(n):
        if n.status == "goal":
            return "goal"
        if n.status in ("invalid", "repeated"):
            return n.status
        if n.id in on_path:
            return "path"
        return "dead"

    style = {
        "path":     ("#e8f1fb", "#1f5fa8", "solid", "#16467d"),
        "goal":     ("#eaf4e0", "#3b6e1e", "solid,bold", "#2d5517"),
        "invalid":  ("#fbe9e9", "#a33a3a", "solid", "#7a2020"),
        "repeated": ("#f1efea", "#9a958c", "dashed", "#6b665e"),
        "dead":     ("#fbefdc", "#8a5a1a", "solid", "#6b4210"),
    }
    mark = {"invalid": " ×", "repeated": " ↺"}

    def move(action):
        parts = [p for p in action.split()[:2] if not p.startswith("0")]
        return "+".join(parts)

    hidden = set()
    for n in walk(root):
        if n.parent is not None and (n.parent.id in hidden or kind(n.parent) == "dead"):
            hidden.add(n.id)
    nodes = [n for n in walk(root) if n.id not in hidden]
    max_d = max(n.depth for n in nodes)
    L = ['digraph tree {',
         '  graph [rankdir=TB, nodesep=0.35, ranksep=0.55, fontname="Helvetica", ordering=out,',
         '         labelloc=t, fontsize=20, label=<<B>BFS search tree: Missionaries &amp; Cannibals</B><BR/>'
         '<FONT POINT-SIZE="12" COLOR="#666666">(M, C, B) = missionaries and cannibals on the left bank, '
         'B = 1 boat on the left, 0 on the right</FONT><BR/> >];',
         '  node [shape=box, style="rounded,filled", fontname="Helvetica", width=1.4, height=0.62, fixedsize=true];',
         '  edge [arrowhead=none, color="#b8b4ac", penwidth=1.1];']
    for d in range(max_d + 1):
        L.append(f'  d{d} [label="d={d}", shape=plaintext, style="", fontcolor="#888888", fontsize=12];')
    L.append("  " + " -> ".join(f"d{d}" for d in range(max_d + 1)) + " [style=invis];")
    for n in nodes:
        k = kind(n)
        fill, border, line, text = style[k]
        sub = "start" if n.parent is None else move(n.action) + mark.get(k, "")
        lbl = (f'<<FONT POINT-SIZE="14" COLOR="{text}"><B>{problem.text(n.state)}</B></FONT><BR/>'
               f'<FONT POINT-SIZE="11" COLOR="{text}">{escape(sub)}</FONT>>')
        L.append(f'  n{n.id} [label={lbl}, fillcolor="{fill}", color="{border}", style="rounded,filled,{line}"];')
        if n.parent is not None:
            pen = ' [color="#1f5fa8", penwidth=2.6]' if n.id in on_path else ""
            L.append(f"  n{n.parent.id} -> n{n.id}{pen};")
    for d in range(max_d + 1):
        same = " ".join(f"n{n.id};" for n in nodes if n.depth == d)
        L.append(f"  {{rank=same; d{d}; {same}}}")
    items = [("path", "Solution path"), ("goal", "Goal"), ("invalid", "Invalid ×"),
             ("repeated", "Repeated ↺"), ("dead", "Dead end")]
    cells = ""
    for k, text in items:
        fill, border, line, _ = style[k]
        cells += (f'<TD WIDTH="18" HEIGHT="18" BGCOLOR="{fill}" COLOR="{border}" BORDER="1"> </TD>'
                  f'<TD ALIGN="LEFT">  {text}        </TD>')
    L.append(f'  legend [shape=plaintext, style="", fixedsize=false, fontsize=12, label=<<TABLE BORDER="0" '
             f'CELLSPACING="2"><TR>{cells}</TR></TABLE>>];')
    L.append(f"  d{max_d} -> legend [style=invis];")
    L.append(f"  n{root.id} -> legend [style=invis, weight=0];")
    L.append("}")
    return "\n".join(L)


def summary(problem, root):
    nodes = list(walk(root))
    count = {k: sum(n.status == k for n in nodes) for k in TAGS}
    goal = next((n for n in nodes if n.status == "goal"), None)
    print(f"\n{problem.name}: {len(nodes)} nodes in the tree | max depth {max(n.depth for n in nodes)} | "
          f"invalid {count['invalid']} | repeated {count['repeated']}"
          + (f" | GOAL at depth {goal.depth}" if goal else ""))
    if goal:
        path = []
        while goal.parent is not None:
            path.append(goal.action)
            goal = goal.parent
        print("Path to the solution: " + " → ".join(reversed(path)))


def main():
    ap = argparse.ArgumentParser(description="Search trees for 8-Puzzle, M&C and RWS")
    ap.add_argument("problem", choices=["8puzzle", "mc", "rws"])
    ap.add_argument("--depth", type=int, help="maximum depth of the tree")
    ap.add_argument("--dot", action="store_true", help="print the tree in Graphviz DOT format")
    a = ap.parse_args()

    problem = {"8puzzle": EightPuzzle, "mc": MissionariesCannibals, "rws": RWS}[a.problem]()
    depth = a.depth if a.depth is not None else {"8puzzle": 3, "mc": 11, "rws": 6}[a.problem]
    root = build_tree(problem, depth)
    if a.dot:
        print(to_dot_simple(problem, root) if getattr(problem, "compact", False) else to_dot(problem, root))
        return
    print_tree(problem, root)
    summary(problem, root)


if __name__ == "__main__":
    main()
