"""
AI Disaster Rescue Simulator  (v2)
----------------------------------
Search ......... BFS, DFS, Greedy Best-First, UCS, A*, Weighted A*
Ordering ....... Severity-first, Nearest-first, Hill Climbing, Simulated Annealing, Brute Force
Allocation ..... CSP backtracking, CSP + MRV + Forward Checking, Greedy
Editable ....... paint the map with the mouse, add/edit/remove victims and teams,
                 save / load scenarios as JSON.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import heapq, json, time, math, random, itertools
from collections import deque

# ───────────────────────── CONFIG ─────────────────────────
ROAD, BLOCKED, DANGER = 0, 1, 2
DANGER_COST = 5                       # moving into a danger cell costs this much
INF = 10 ** 6
CELL = 56
SKILLS = ["Medical", "Technical", "Fire", "Water"]
URGENCY = {1: 1, 2: 3, 3: 6}          # severity -> waiting penalty per time unit
SEARCH_ALGOS = ["BFS", "DFS", "Greedy", "UCS", "A*", "Weighted A*"]
ORDER_ALGOS = ["Severity First", "Nearest First", "Hill Climbing",
               "Simulated Annealing", "Brute Force"]
CSP_ALGOS = ["Plain Backtracking", "MRV + Forward Checking", "Greedy (no backtrack)"]

BG, PANEL, FG, MUTED = "#0f172a", "#1e293b", "#e2e8f0", "#94a3b8"
ACCENT = "#38bdf8"
COL = {ROAD: "#334155", BLOCKED: "#991b1b", DANGER: "#b45309"}
SEV_COL = {1: "#22c55e", 2: "#facc15", 3: "#f43f5e"}


# ───────────────────────── MODEL ─────────────────────────
class World:
    def __init__(self):
        self.reset_default()

    def reset_default(self):
        self.grid = [
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 2, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 1, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]]
        self.base = (0, 0)
        self.victims = [
            {"id": "V1", "pos": (2, 5), "severity": 3, "skill": "Medical"},
            {"id": "V2", "pos": (4, 2), "severity": 2, "skill": "Technical"},
            {"id": "V3", "pos": (6, 7), "severity": 1, "skill": "Medical"}]
        self.teams = [
            {"name": "Team A", "skills": ["Medical", "Technical"], "capacity": 2},
            {"name": "Team B", "skills": ["Medical"], "capacity": 2},
            {"name": "Team C", "skills": ["Technical"], "capacity": 2}]
        self.cache = {}

    # ---- grid helpers ----
    @property
    def rows(self): return len(self.grid)
    @property
    def cols(self): return len(self.grid[0])

    def changed(self): self.cache.clear()

    def valid(self, p):
        r, c = p
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] != BLOCKED

    def neighbors(self, p):
        r, c = p
        return [q for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if self.valid(q)]

    def cost(self, p):
        return DANGER_COST if self.grid[p[0]][p[1]] == DANGER else 1

    @staticmethod
    def h(a, b):                      # Manhattan: admissible because min step cost = 1
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def next_id(self):
        n = 1
        used = {v["id"] for v in self.victims}
        while f"V{n}" in used: n += 1
        return f"V{n}"

    # ---- 1. PATH SEARCH ----
    def search(self, start, goal, algo):
        t0 = time.perf_counter()
        parent, order = {}, []
        found = False
        if algo in ("BFS", "DFS"):
            frontier, seen = deque([start]), {start}
            while frontier:
                cur = frontier.popleft() if algo == "BFS" else frontier.pop()
                order.append(cur)
                if cur == goal:
                    found = True
                    break
                for n in self.neighbors(cur):
                    if n not in seen:
                        seen.add(n); parent[n] = cur; frontier.append(n)
        else:
            wg, wh = {"Greedy": (0, 1), "UCS": (1, 0), "A*": (1, 1), "Weighted A*": (1, 2)}[algo]
            g, closed, tie = {start: 0}, set(), itertools.count()
            heap = [(0, next(tie), start)]
            while heap:
                _, _, cur = heapq.heappop(heap)
                if cur in closed: continue
                closed.add(cur); order.append(cur)
                if cur == goal:
                    found = True
                    break
                for n in self.neighbors(cur):
                    ng = g[cur] + self.cost(n)
                    if algo == "Greedy":
                        if n in g: continue
                    elif ng >= g.get(n, INF):
                        continue
                    g[n] = ng; parent[n] = cur
                    heapq.heappush(heap, (wg * ng + wh * self.h(n, goal), next(tie), n))
        path, total = None, INF
        if found:
            path, node = [goal], goal
            while node in parent:
                node = parent[node]; path.append(node)
            path.reverse()
            total = sum(self.cost(p) for p in path[1:])
        return {"found": found, "path": path, "cost": total, "order": order,
                "expanded": len(order), "ms": (time.perf_counter() - t0) * 1000}

    def dist(self, a, b):
        key = (a, b)
        if key not in self.cache:
            self.cache[key] = self.search(a, b, "A*")["cost"]
        return self.cache[key]

    # ---- 2. VICTIM ORDERING ----
    def score(self, order):
        cur, elapsed, total = self.base, 0, 0
        for v in order:
            d = self.dist(cur, v["pos"])
            if d >= INF: return INF
            elapsed += d
            total += d + URGENCY[v["severity"]] * elapsed
            cur = v["pos"]
        return total

    def plan(self, algo):
        t0 = time.perf_counter()
        vs = self.victims
        by_sev = sorted(vs, key=lambda v: -v["severity"])
        if algo == "Severity First":
            order = by_sev
        elif algo == "Nearest First":
            left, order, cur = vs[:], [], self.base
            while left:
                nxt = min(left, key=lambda v: self.dist(cur, v["pos"]))
                order.append(nxt); left.remove(nxt); cur = nxt["pos"]
        elif algo == "Hill Climbing":
            order = by_sev[:]
            improved = True
            while improved:
                improved, best = False, self.score(order)
                for i in range(len(order)):
                    for j in range(i + 1, len(order)):
                        new = order[:]; new[i], new[j] = new[j], new[i]
                        s = self.score(new)
                        if s < best:
                            order, best, improved = new, s, True
        elif algo == "Simulated Annealing":
            rnd = random.Random(1)
            cur = by_sev[:]; cs = self.score(cur); order, bs = cur[:], cs
            T = 50.0
            while T > 0.05 and len(cur) > 1:
                i, j = rnd.sample(range(len(cur)), 2)
                new = cur[:]; new[i], new[j] = new[j], new[i]
                ns = self.score(new)
                if ns < cs or rnd.random() < math.exp(-(ns - cs) / T):
                    cur, cs = new, ns
                    if cs < bs: order, bs = cur[:], cs
                T *= 0.97
        elif algo == "Brute Force":
            if len(vs) > 7: return None
            order = list(min(itertools.permutations(vs), key=self.score))
        return {"order": list(order), "score": self.score(order),
                "ms": (time.perf_counter() - t0) * 1000}

    # ---- 3. CSP: TEAM ALLOCATION ----
    def csp(self, mode):
        t0 = time.perf_counter()
        cap = {t["name"]: t["capacity"] for t in self.teams}
        ok = {v["id"]: [t["name"] for t in self.teams if v["skill"] in t["skills"]]
              for v in self.victims}
        res, nodes = {}, [0]
        dom = lambda v: [n for n in ok[v["id"]] if cap[n] > 0]

        if mode.startswith("Greedy"):
            for v in sorted(self.victims, key=lambda v: -v["severity"]):
                d = dom(v)
                if not d: res = None; break
                n = max(d, key=lambda x: cap[x]); res[v["id"]] = n; cap[n] -= 1; nodes[0] += 1
        else:
            fc = mode.startswith("MRV")
            def bt(rem):
                if not rem: return True
                v = min(rem, key=lambda x: len(dom(x))) if fc else rem[0]
                rest = [x for x in rem if x is not v]
                for n in dom(v):
                    nodes[0] += 1
                    res[v["id"]] = n; cap[n] -= 1
                    if not (fc and any(not dom(x) for x in rest)) and bt(rest):
                        return True
                    cap[n] += 1; del res[v["id"]]
                return False
            if not bt(self.victims[:]): res = None
        return {"assign": res, "nodes": nodes[0], "ms": (time.perf_counter() - t0) * 1000}

    # ---- save / load ----
    def to_json(self):
        return {"grid": self.grid, "base": list(self.base), "teams": self.teams,
                "victims": [dict(v, pos=list(v["pos"])) for v in self.victims]}

    def from_json(self, d):
        self.grid = d["grid"]; self.base = tuple(d["base"]); self.teams = d["teams"]
        self.victims = [dict(v, pos=tuple(v["pos"])) for v in d["victims"]]
        self.changed()


# ───────────────────────── GUI ─────────────────────────
class RescueApp:
    def __init__(self, root):
        self.root, self.w = root, World()
        self.path, self.explored, self.job, self.step = [], set(), None, -1
        root.title("AI Disaster Rescue Simulator")
        root.configure(bg=BG)
        self.style()
        self.menu()

        ttk.Label(root, text="🚑  AI DISASTER RESCUE SIMULATOR", style="Title.TLabel").pack(pady=(10, 2))
        ttk.Label(root, text="Paint the map, move victims, then compare AI algorithms.",
                  style="Muted.TLabel").pack()

        # toolbar
        bar = ttk.Frame(root); bar.pack(fill="x", padx=12, pady=6)
        ttk.Label(bar, text="Edit tool:", style="Muted.TLabel").pack(side="left", padx=(0, 6))
        self.tool = tk.StringVar(value="Road")
        for t in ("Road", "Blocked", "Danger", "Base", "Add/Edit Victim", "Remove Victim"):
            ttk.Radiobutton(bar, text=t, value=t, variable=self.tool, style="Tool.TRadiobutton").pack(side="left", padx=3)

        body = ttk.Frame(root); body.pack(padx=12)
        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=1, highlightbackground=PANEL)
        self.canvas.grid(row=0, column=0, sticky="n")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Motion>", self.on_hover)

        side = ttk.Notebook(body); side.grid(row=0, column=1, padx=(12, 0), sticky="n")
        self.build_route_tab(side); self.build_compare_tab(side)
        self.build_order_tab(side); self.build_alloc_tab(side); self.build_data_tab(side)

        legend = ("Road  •  Blocked (X)  •  Danger (!, cost 5)  •  Base (B)  •  "
                  "Victim circle colour = severity (green 1, yellow 2, red 3)")
        ttk.Label(root, text=legend, style="Muted.TLabel").pack(pady=(6, 0))

        self.out = tk.Text(root, width=100, height=11, bg=PANEL, fg=FG, insertbackground=FG,
                           relief="flat", font=("Consolas", 10), padx=8, pady=6)
        self.out.pack(padx=12, pady=8)
        self.statusbar = ttk.Label(root, text="Ready", style="Muted.TLabel")
        self.statusbar.pack(anchor="w", padx=12, pady=(0, 6))
        self.refresh_all()

    # ---------- styling ----------
    def style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL, font=("Segoe UI", 10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=ACCENT)
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("TButton", background=PANEL, foreground=FG, padding=5, borderwidth=0)
        s.map("TButton", background=[("active", "#334155")])
        s.configure("Accent.TButton", background=ACCENT, foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        s.map("Accent.TButton", background=[("active", "#7dd3fc")])
        s.configure("Tool.TRadiobutton", background=BG, foreground=FG)
        s.map("Tool.TRadiobutton", foreground=[("selected", ACCENT)], background=[("active", BG)])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(10, 5))
        s.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#0f172a")])
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG, rowheight=24, borderwidth=0)
        s.configure("Treeview.Heading", background="#334155", foreground=FG, font=("Segoe UI", 9, "bold"))
        s.map("Treeview", background=[("selected", "#0369a1")])
        s.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=FG)

    def menu(self):
        m = tk.Menu(self.root); f = tk.Menu(m, tearoff=0)
        f.add_command(label="Save scenario…", command=self.save)
        f.add_command(label="Load scenario…", command=self.load)
        f.add_separator()
        f.add_command(label="Random map", command=self.randomize)
        f.add_command(label="Clear map", command=self.clear_map)
        f.add_command(label="Restore default scenario", command=self.restore)
        m.add_cascade(label="File", menu=f); self.root.config(menu=m)

    # ---------- tabs ----------
    def tab(self, nb, title):
        f = ttk.Frame(nb, padding=8); nb.add(f, text=title); return f

    def table(self, parent, cols, widths, height=7):
        t = ttk.Treeview(parent, columns=cols, show="headings", height=height, selectmode="browse")
        for c, wd in zip(cols, widths):
            t.heading(c, text=c); t.column(c, width=wd, anchor="center")
        return t

    def build_route_tab(self, nb):
        f = self.tab(nb, "Route")
        self.vic = tk.StringVar(); self.algo = tk.StringVar(value="A*"); self.oalgo = tk.StringVar(value="Hill Climbing")
        ttk.Label(f, text="Victim").pack(anchor="w")
        self.vcombo = ttk.Combobox(f, textvariable=self.vic, state="readonly", width=28); self.vcombo.pack(pady=(0, 6))
        ttk.Label(f, text="Path-finding algorithm").pack(anchor="w")
        ttk.Combobox(f, textvariable=self.algo, values=SEARCH_ALGOS, state="readonly", width=28).pack(pady=(0, 6))
        ttk.Label(f, text="Victim-ordering algorithm").pack(anchor="w")
        ttk.Combobox(f, textvariable=self.oalgo, values=ORDER_ALGOS, state="readonly", width=28).pack(pady=(0, 8))
        for txt, cmd, sty in [("Find Route", self.find_route, "Accent.TButton"),
                              ("Animate Search", lambda: self.find_route(True), "TButton"),
                              ("Next Victim (mission order)", self.next_victim, "TButton"),
                              ("Show Complete Mission", self.complete_route, "TButton"),
                              ("Clear Overlay", self.reset, "TButton")]:
            ttk.Button(f, text=txt, command=cmd, style=sty, width=30).pack(pady=3)

    def build_compare_tab(self, nb):
        f = self.tab(nb, "Compare Search")
        self.ctree = self.table(f, ("Algorithm", "Cost", "Steps", "Expanded", "ms", "Optimal"),
                                (100, 50, 50, 70, 55, 60))
        self.ctree.pack()
        self.ctree.bind("<Double-1>", self.show_compared)
        ttk.Button(f, text="Compare for selected victim", style="Accent.TButton",
                   command=self.compare_one).pack(fill="x", pady=(6, 2))
        ttk.Button(f, text="Compare over ALL victims (totals)", command=self.compare_all).pack(fill="x")
        ttk.Label(f, text="Double-click a row to draw that algorithm's\nexplored cells and path.",
                  style="Muted.TLabel").pack(pady=4)
        self.cres = {}

    def build_order_tab(self, nb):
        f = self.tab(nb, "Compare Ordering")
        self.otree = self.table(f, ("Algorithm", "Order", "Score", "ms"), (130, 130, 60, 50))
        self.otree.pack()
        self.otree.bind("<Double-1>", self.use_order)
        ttk.Button(f, text="Compare ordering algorithms", style="Accent.TButton",
                   command=self.compare_order).pack(fill="x", pady=(6, 2))
        ttk.Label(f, text="Score = travel + severity-weight × elapsed time.\nLower is better. Double-click to show "
                          "that mission.", style="Muted.TLabel").pack(pady=4)

    def build_alloc_tab(self, nb):
        f = self.tab(nb, "Team Allocation")
        self.atree = self.table(f, ("Algorithm", "Nodes", "ms", "Result"), (150, 50, 50, 150), height=5)
        self.atree.pack()
        ttk.Button(f, text="Run CSP solvers", style="Accent.TButton",
                   command=self.run_csp).pack(fill="x", pady=(6, 2))
        ttk.Label(f, text="Each victim needs a team with the right skill;\nteams have limited capacity.",
                  style="Muted.TLabel").pack(pady=4)

    def build_data_tab(self, nb):
        f = self.tab(nb, "Edit Data")
        ttk.Label(f, text="Victims (add them by clicking the map)").pack(anchor="w")
        self.vtree = self.table(f, ("ID", "Position", "Severity", "Skill"), (50, 80, 70, 100), height=4)
        self.vtree.pack()
        r = ttk.Frame(f); r.pack(pady=3)
        ttk.Button(r, text="Edit", command=self.edit_victim).pack(side="left", padx=2)
        ttk.Button(r, text="Delete", command=self.del_victim).pack(side="left", padx=2)
        ttk.Label(f, text="Rescue teams").pack(anchor="w", pady=(6, 0))
        self.ttree = self.table(f, ("Team", "Skills", "Capacity"), (80, 180, 70), height=4)
        self.ttree.pack()
        r = ttk.Frame(f); r.pack(pady=3)
        for txt, cmd in (("Add", self.add_team), ("Edit", self.edit_team), ("Delete", self.del_team)):
            ttk.Button(r, text=txt, command=cmd).pack(side="left", padx=2)

    # ---------- dialogs / logging ----------
    def log(self, text, clear=True):
        if clear: self.out.delete("1.0", tk.END)
        self.out.insert(tk.END, text + "\n")

    def form(self, title, fields):
        top = tk.Toplevel(self.root); top.title(title); top.configure(bg=BG, padx=10, pady=10)
        top.transient(self.root); top.grab_set()
        vs, result = {}, {}
        for i, (key, label, default, opts) in enumerate(fields):
            ttk.Label(top, text=label).grid(row=i, column=0, sticky="w", pady=4, padx=4)
            v = tk.StringVar(value=str(default)); vs[key] = v
            w = ttk.Combobox(top, textvariable=v, values=opts, state="readonly") if opts else ttk.Entry(top, textvariable=v)
            w.grid(row=i, column=1, pady=4, padx=4)
        def ok():
            result.update({k: v.get() for k, v in vs.items()}); top.destroy()
        ttk.Button(top, text="Save", style="Accent.TButton", command=ok).grid(columnspan=2, pady=8)
        self.root.wait_window(top)
        return result or None

    # ---------- map drawing ----------
    def draw(self):
        c, w = self.canvas, self.w
        c.config(width=w.cols * CELL, height=w.rows * CELL)
        c.delete("all")
        for r in range(w.rows):
            for col in range(w.cols):
                x, y = col * CELL, r * CELL
                t = w.grid[r][col]
                color = "#0e7490" if (r, col) in self.explored and t == ROAD else COL[t]
                c.create_rectangle(x, y, x + CELL, y + CELL, fill=color, outline=BG)
                if t == BLOCKED: c.create_text(x + CELL / 2, y + CELL / 2, text="✕", fill="#fecaca", font=("Arial", 16, "bold"))
                if t == DANGER: c.create_text(x + CELL / 2, y + CELL / 2, text="⚠", fill="#fde68a", font=("Arial", 16))
        if len(self.path) > 1:
            pts = [v for r, col in self.path for v in (col * CELL + CELL / 2, r * CELL + CELL / 2)]
            c.create_line(*pts, fill=ACCENT, width=5, arrow=tk.LAST, capstyle="round", joinstyle="round")
        br, bc = w.base
        c.create_rectangle(bc * CELL + 6, br * CELL + 6, bc * CELL + CELL - 6, br * CELL + CELL - 6,
                           fill="#2563eb", outline="white", width=2)
        c.create_text(bc * CELL + CELL / 2, br * CELL + CELL / 2, text="BASE", fill="white", font=("Arial", 9, "bold"))
        for v in w.victims:
            r, col = v["pos"]; cx, cy = col * CELL + CELL / 2, r * CELL + CELL / 2
            c.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill=SEV_COL[v["severity"]], outline="white", width=2)
            c.create_text(cx, cy - 4, text=v["id"], fill="#0f172a", font=("Arial", 10, "bold"))
            c.create_text(cx, cy + 9, text=v["skill"][0], fill="#0f172a", font=("Arial", 8))

    def refresh_all(self):
        w = self.w
        ids = [v["id"] for v in w.victims]
        self.vcombo["values"] = ids
        if self.vic.get() not in ids: self.vic.set(ids[0] if ids else "")
        self.vtree.delete(*self.vtree.get_children())
        for v in w.victims:
            self.vtree.insert("", "end", iid=v["id"], values=(v["id"], v["pos"], v["severity"], v["skill"]))
        self.ttree.delete(*self.ttree.get_children())
        for i, t in enumerate(w.teams):
            self.ttree.insert("", "end", iid=str(i), values=(t["name"], ", ".join(t["skills"]), t["capacity"]))
        self.draw()

    def edited(self):
        self.stop(); self.path, self.explored, self.step = [], set(), -1
        self.w.changed(); self.refresh_all()

    # ---------- map editing ----------
    def cell(self, e):
        r, c = e.y // CELL, e.x // CELL
        return (r, c) if 0 <= r < self.w.rows and 0 <= c < self.w.cols else None

    def victim_at(self, p):
        return next((v for v in self.w.victims if v["pos"] == p), None)

    def paint(self, p):
        t, w = self.tool.get(), self.w
        code = {"Road": ROAD, "Blocked": BLOCKED, "Danger": DANGER}.get(t)
        if code is None: return
        if code == BLOCKED and (p == w.base or self.victim_at(p)):
            return
        if w.grid[p[0]][p[1]] != code:
            w.grid[p[0]][p[1]] = code; self.edited()

    def on_drag(self, e):
        p = self.cell(e)
        if p: self.paint(p)

    def on_click(self, e):
        p = self.cell(e)
        if not p: return
        t, w = self.tool.get(), self.w
        if t in ("Road", "Blocked", "Danger"):
            self.paint(p)
        elif t == "Base":
            if w.grid[p[0]][p[1]] != BLOCKED: w.base = p; self.edited()
        elif t == "Remove Victim":
            v = self.victim_at(p)
            if v: w.victims.remove(v); self.edited()
        else:
            if w.grid[p[0]][p[1]] == BLOCKED or p == w.base:
                return self.statusbar.config(text="Can't place a victim on a blocked cell or the base.")
            v = self.victim_at(p)
            self.victim_dialog(v, p)

    def victim_dialog(self, v, p=None):
        r = self.form("Victim", [("sev", "Severity (1-3)", v["severity"] if v else 2, ["1", "2", "3"]),
                                 ("skill", "Skill needed", v["skill"] if v else SKILLS[0], SKILLS)])
        if not r: return
        if v: v["severity"], v["skill"] = int(r["sev"]), r["skill"]
        else: self.w.victims.append({"id": self.w.next_id(), "pos": p, "severity": int(r["sev"]), "skill": r["skill"]})
        self.edited()

    def on_hover(self, e):
        p = self.cell(e)
        if p:
            names = ["Road", "Blocked", "Danger"]
            v = self.victim_at(p)
            extra = f" | victim {v['id']} (sev {v['severity']}, {v['skill']})" if v else ""
            self.statusbar.config(text=f"Cell {p} - {names[self.w.grid[p[0]][p[1]]]}{extra}")

    # ---------- data tab actions ----------
    def edit_victim(self):
        s = self.vtree.selection()
        if s: self.victim_dialog(next(v for v in self.w.victims if v["id"] == s[0]))

    def del_victim(self):
        s = self.vtree.selection()
        if s: self.w.victims = [v for v in self.w.victims if v["id"] != s[0]]; self.edited()

    def team_dialog(self, t=None):
        r = self.form("Team", [("name", "Name", t["name"] if t else f"Team {len(self.w.teams) + 1}", None),
                               ("skills", "Skills (comma separated)", ", ".join(t["skills"]) if t else "Medical", None),
                               ("cap", "Capacity", t["capacity"] if t else 2, None)])
        if not r: return None
        try:
            cap = int(r["cap"])
        except ValueError:
            return messagebox.showerror("Invalid", "Capacity must be a whole number.")
        return {"name": r["name"], "skills": [s.strip() for s in r["skills"].split(",") if s.strip()], "capacity": cap}

    def add_team(self):
        t = self.team_dialog()
        if t: self.w.teams.append(t); self.edited()

    def edit_team(self):
        s = self.ttree.selection()
        if s:
            t = self.team_dialog(self.w.teams[int(s[0])])
            if t: self.w.teams[int(s[0])] = t; self.edited()

    def del_team(self):
        s = self.ttree.selection()
        if s: del self.w.teams[int(s[0])]; self.edited()

    # ---------- route tab ----------
    def selected_victim(self):
        return next((v for v in self.w.victims if v["id"] == self.vic.get()), None)

    def show_search(self, res, title, animate=False):
        if not res["found"]:
            self.path, self.explored = [], set(); self.draw()
            return self.log(f"{title}: NO ROUTE (victim is cut off by blocked cells).")
        self.log(f"{title}\n  Path ({len(res['path']) - 1} steps): {res['path']}\n"
                 f"  Movement cost: {res['cost']}    Nodes expanded: {res['expanded']}    Time: {res['ms']:.3f} ms")
        self.stop()
        if animate: self.animate(res)
        else: self.path, self.explored = res["path"], set(res["order"]); self.draw()

    def find_route(self, animate=False):
        v = self.selected_victim()
        if not v: return self.log("No victim selected.")
        algo = self.algo.get()
        self.show_search(self.w.search(self.w.base, v["pos"], algo), f"{algo} route to {v['id']}", animate)

    def next_victim(self):
        plan = self.w.plan(self.oalgo.get())
        if not plan or not plan["order"]: return self.log("No victims.")
        self.step = (self.step + 1) % len(plan["order"])
        v = plan["order"][self.step]; self.vic.set(v["id"])
        self.find_route()

    def complete_route(self):
        plan = self.w.plan(self.oalgo.get())
        if not plan: return self.log("Brute force limited to 7 victims.")
        self.show_mission(plan["order"], self.oalgo.get())

    def show_mission(self, order, label):
        cur, full, total, lines = self.w.base, [], 0, []
        for v in order:
            res = self.w.search(cur, v["pos"], self.algo.get())
            if not res["found"]:
                return self.log(f"{v['id']} is unreachable - mission impossible.")
            full += res["path"] if not full else res["path"][1:]
            total += res["cost"]
            lines.append(f"  {v['id']} (sev {v['severity']}) at {v['pos']}: leg cost {res['cost']}")
            cur = v["pos"]
        self.stop(); self.path, self.explored = full, set()
        self.draw()
        self.log(f"COMPLETE MISSION  [{label} order, {self.algo.get()} paths]\n" + "\n".join(lines) +
                 f"\n  Total movement cost: {total}\n  Mission score: {self.w.score(order)}")

    def reset(self):
        self.stop(); self.path, self.explored, self.step = [], set(), -1
        self.draw(); self.log("Overlay cleared.")

    # ---------- animation ----------
    def stop(self):
        if self.job: self.root.after_cancel(self.job); self.job = None

    def animate(self, res):
        self.path, self.explored = [], set()
        seq, i = res["order"], [0]
        def tick():
            for _ in range(max(1, len(seq) // 50)):
                if i[0] < len(seq): self.explored.add(seq[i[0]]); i[0] += 1
            if i[0] >= len(seq): self.path = res["path"]; self.job = None
            else: self.job = self.root.after(30, tick)
            self.draw()
        tick()

    # ---------- comparisons ----------
    def compare_one(self):
        v = self.selected_victim()
        if not v: return self.log("No victim selected.")
        self.cres = {a: self.w.search(self.w.base, v["pos"], a) for a in SEARCH_ALGOS}
        best = min(r["cost"] for r in self.cres.values())
        self.ctree.delete(*self.ctree.get_children())
        for a, r in self.cres.items():
            ok = "✔" if r["found"] and r["cost"] == best else ("—" if not r["found"] else "✘")
            self.ctree.insert("", "end", iid=a, values=(
                a, r["cost"] if r["found"] else "n/a", len(r["path"]) - 1 if r["found"] else "-",
                r["expanded"], f"{r['ms']:.2f}", ok))
        self.log(f"Search comparison for base -> {v['id']} {v['pos']}\n"
                 "  Cost = real movement cost (danger = 5). Optimal = matches the cheapest path found.\n"
                 "  BFS ignores costs, DFS ignores everything, Greedy chases the heuristic,\n"
                 "  UCS and A* are optimal; A* expands fewer nodes. Weighted A* is faster but may be sub-optimal.")

    def compare_all(self):
        self.ctree.delete(*self.ctree.get_children()); self.cres = {}
        rows = {}
        for a in SEARCH_ALGOS:
            cost = exp = steps = 0; ms = 0.0
            for v in self.w.victims:
                r = self.w.search(self.w.base, v["pos"], a)
                if r["found"]: cost += r["cost"]; steps += len(r["path"]) - 1
                exp += r["expanded"]; ms += r["ms"]
            rows[a] = (cost, steps, exp, ms)
        best = min(r[0] for r in rows.values()) if rows else 0
        for a, (cost, steps, exp, ms) in rows.items():
            self.ctree.insert("", "end", values=(a, cost, steps, exp, f"{ms:.2f}", "✔" if cost == best else "✘"))
        self.log("Totals over all victims (base -> each victim).")

    def show_compared(self, _):
        s = self.ctree.selection()
        if s and s[0] in self.cres:
            self.show_search(self.cres[s[0]], f"{s[0]} route to {self.vic.get()}")

    def compare_order(self):
        self.otree.delete(*self.otree.get_children()); self.oplans = {}
        for a in ORDER_ALGOS:
            p = self.w.plan(a)
            if not p:
                self.otree.insert("", "end", iid=a, values=(a, "skipped (>7)", "-", "-")); continue
            self.oplans[a] = p
            sc = p["score"] if p["score"] < INF else "unreachable"
            self.otree.insert("", "end", iid=a, values=(a, " → ".join(v["id"] for v in p["order"]), sc, f"{p['ms']:.2f}"))
        self.log("Ordering comparison. Brute Force is the true optimum (when ≤7 victims);\n"
                 "Hill Climbing / Annealing are heuristics that usually match it far faster on bigger problems.")

    def use_order(self, _):
        s = self.otree.selection()
        if s and s[0] in getattr(self, "oplans", {}):
            self.oalgo.set(s[0]); self.show_mission(self.oplans[s[0]]["order"], s[0])

    def run_csp(self):
        self.atree.delete(*self.atree.get_children()); lines = []
        for m in CSP_ALGOS:
            r = self.w.csp(m)
            txt = ", ".join(f"{k}→{v}" for k, v in sorted(r["assign"].items())) if r["assign"] is not None else "NO SOLUTION"
            self.atree.insert("", "end", values=(m, r["nodes"], f"{r['ms']:.2f}", txt))
            lines.append(f"{m}: {txt}")
        self.log("RESCUE TEAM ALLOCATION (CSP)\n" + "\n".join(lines) +
                 "\n\nNodes = assignments tried. MRV+FC picks the most constrained victim first and prunes early.")

    # ---------- scenario tools ----------
    def save(self):
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Scenario", "*.json")])
        if f:
            with open(f, "w") as fh: json.dump(self.w.to_json(), fh, indent=2)

    def load(self):
        f = filedialog.askopenfilename(filetypes=[("Scenario", "*.json")])
        if f:
            try:
                with open(f) as fh: self.w.from_json(json.load(fh))
                self.edited()
            except Exception as ex:
                messagebox.showerror("Load failed", str(ex))

    def randomize(self):
        w = self.w
        keep = {w.base} | {v["pos"] for v in w.victims}
        for r in range(w.rows):
            for c in range(w.cols):
                x = random.random()
                w.grid[r][c] = ROAD if (r, c) in keep or x < 0.68 else (BLOCKED if x < 0.88 else DANGER)
        self.edited()

    def clear_map(self):
        self.w.grid = [[ROAD] * self.w.cols for _ in range(self.w.rows)]; self.edited()

    def restore(self):
        self.w.reset_default(); self.edited()


if __name__ == "__main__":
    root = tk.Tk()
    RescueApp(root)
    root.mainloop()
    