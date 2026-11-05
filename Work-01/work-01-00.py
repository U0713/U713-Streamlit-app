# -*- coding: utf-8 -*-
"""
KDS 64 10 07 (2026) 4.4.12  파고 전달율(Kt) / 전달파고(Ht) 계산  (조위 1개)

 ① 직립혼성제(무공)      : 참고식 (4.4-83), (4.4-86)
 ② TTP 피복 경사제       : 참고식 (4.4-84), (4.4-85)   [2층 정적피복, 직각입사]
 ③ 수중구조물(잠제·인공리프): 참고식 (4.4-87) 투과형 / (4.4-88) 경사형 / (4.4-89) 불투과형

계산식 칸은 위에서 아래 순서로 계산되며, 앞 칸의 결과를 뒤 칸에서 변수로 쓸 수 있습니다.
사용 변수 : Hs(=H1/3), Ts, L(전면수심 h에서 유의주기 파장), h(수심), s(=Hs/L),
            Rc(여유고 = 마루고 - 조위, 정수면 위 +), Dc(마루수심 = 조위 - 마루고, 수중구조물의 Rc),
            hm(근고부 상단수심 h'), W(어깨폭 또는 마루폭), Dn(TTP 공칭길이 = V^(1/3))
사용 함수 : exp ln log sqrt tanh pi min max abs
"""
import math
import tkinter as tk
from tkinter import ttk, messagebox

G = 9.80665
SAFE = {"exp": math.exp, "ln": math.log, "log": math.log, "sqrt": math.sqrt,
        "tanh": math.tanh, "pi": math.pi, "min": min, "max": max, "abs": abs}

_SUB_IN = [("bed", "해저고 (DL m)", "-10.0"),
           ("crest", "구조물 상단고 (DL m)", "-2.0"),
           ("W", "마루폭 W (m)", "20.0")]


def _sub(eq, f):
    return dict(inputs=_SUB_IN, formulas=[("Kt", f"Kt (4.4-{eq})", f)])


TYPES = {
    "직립혼성제(무공)": dict(
        inputs=[("bed", "전면 해저고 (DL m)", "-12.0"),
                ("crest", "직립부 마루높이 (DL m)", "6.0"),
                ("mound", "근고부(마운드) 상단 (DL m)", "-8.0")],
        formulas=[("Kto", "Kto 월파 (4.4-86 1항)", "3.17*exp(-1.67*(Rc/Hs)**0.36*s**(-0.24))"),
                  ("Ktp", "Ktp 투과 (4.4-86 2항)", "sqrt(0.014*(1-hm/h)**2)"),
                  ("Kt", "Kt 합성 (4.4-83)", "sqrt(Kto**2 + Ktp**2)")]),
    "TTP 피복 경사제": dict(
        inputs=[("bed", "전면 해저고 (DL m)", "-10.0"),
                ("crest", "상치콘크리트 마루높이 (DL m)", "7.0"),
                ("W", "상치콘크리트 전면 피복재 어깨폭 W (m)", "8.0"),
                ("V", "TTP 체적 V (m³)", "25.0")],
        formulas=[("a_s", "α_s (4.4-85)", "5*s+0.233"),
                  ("a_row", "α_row (4.4-85)", "0.0143*(W/Dn)-0.0331"),
                  ("Kt", "Kt (4.4-84)", "max(a_s-0.31*(Rc/Hs)-a_row, 0.06)")]),
    "수중구조물-투과형": _sub(87, "0.380*exp(Dc/h)+0.095*exp(Dc/Hs)+0.072*ln(Hs/L)-0.188*ln(W/L)+0.013"),
    "수중구조물-경사형": _sub(88, "0.278*exp(Dc/h)+0.146*exp(Dc/Hs)+0.075*ln(Hs/L)-0.205*ln(W/L)-0.015"),
    "수중구조물-불투과형": _sub(89, "0.483*exp(Dc/h)+0.093*exp(Dc/Hs)+0.019*ln(Hs/L)-0.157*ln(W/L)-0.376"),
}


def wavelength(T, h):
    L0 = G * T ** 2 / (2 * math.pi)
    L = L0
    for _ in range(300):
        Ln = L0 * math.tanh(2 * math.pi * h / L)
        if abs(Ln - L) < 1e-9:
            break
        L = Ln
    return L


def ev(expr, ns):
    if not expr.strip():
        raise ValueError("계산식 칸이 비어 있습니다.")
    return eval(expr, {"__builtins__": {}}, {**SAFE, **ns})


def calculate(tname, v, tide, Hs, Ts, forms):
    h = tide - v["bed"]
    if h <= 0:
        raise ValueError("조위가 해저고보다 낮습니다.")
    L = wavelength(Ts, h)
    ns = dict(Hs=Hs, Ts=Ts, L=L, h=h, s=Hs / L, Rc=v["crest"] - tide, Dc=tide - v["crest"],
              W=v.get("W", 0.0), V=v.get("V", 0.0))
    ns["Dn"] = ns["V"] ** (1 / 3) if ns["V"] > 0 else 1.0
    if "mound" in v:
        ns["hm"] = tide - v["mound"]
    inter = {}
    for name, _, _ in TYPES[tname]["formulas"]:
        ns[name] = inter[name] = ev(forms[name], ns)
    Kt = ns["Kt"]

    warn = []
    def chk(label, val, lo, hi):
        if not lo <= val <= hi:
            warn.append(f"{label} = {val:.3f} : 적용범위({lo}~{hi}) 벗어남")
    if tname.startswith("직립혼성제"):
        chk("Rc/Hs", ns["Rc"] / Hs, 0.3, 2.6); chk("Hs/L", ns["s"], 0.02, 0.05)
        chk("h'/h", ns["hm"] / h, 0.5, 1.0)
    elif tname.startswith("TTP"):
        chk("Hs/L(s)", ns["s"], 0.015, 0.044); chk("Rc/Hs", ns["Rc"] / Hs, 0.6, 2.0)
        chk("W/Dn", ns["W"] / ns["Dn"], 2.32, 5.12)
        if ns["Rc"] <= 0: warn.append("조위가 마루높이 이상입니다.")
    else:
        if ns["Dc"] <= 0: warn.append("구조물 상단이 정수면 위입니다 (수중구조물 아님).")
        chk("Hs/L", ns["s"], 0.01, 0.065); chk("W/L", ns["W"] / L, 0.04, 1.5)
    return dict(h=h, L=L, s=ns["s"], Rc=ns["Rc"], Dc=ns["Dc"], inter=inter, Kt=Kt,
                Ht=Kt * Hs, Tt=0.65 * Ts, warn=warn)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("파고 전달율 계산 | KDS 64 10 07 4.4.12")
        self.geometry("1100x660")
        self.left = ttk.Frame(self, padding=8); self.left.pack(side="left", fill="y")
        right = ttk.Frame(self, padding=8); right.pack(side="left", fill="both", expand=True)

        g = ttk.LabelFrame(self.left, text="1. 구조물 형식", padding=6); g.pack(fill="x", pady=3)
        self.tsel = tk.StringVar(value=list(TYPES)[0])
        cb = ttk.Combobox(g, textvariable=self.tsel, values=list(TYPES), state="readonly", width=26)
        cb.pack(); cb.bind("<<ComboboxSelected>>", lambda e: self.build())

        g = ttk.LabelFrame(self.left, text="2. 설계파 (구조물 위치 입사파)", padding=6); g.pack(fill="x", pady=3)
        self.Hs, self.Ts = tk.StringVar(value="6.0"), tk.StringVar(value="12.0")
        for i, (l, var) in enumerate([("유의파고 Hs (m)", self.Hs), ("유의주기 Ts (s)", self.Ts)]):
            ttk.Label(g, text=l).grid(row=i, column=0, sticky="w")
            ttk.Entry(g, textvariable=var, width=10).grid(row=i, column=1)

        g = ttk.LabelFrame(self.left, text="3. 조위 (DL m)", padding=6); g.pack(fill="x", pady=3)
        self.tide = tk.StringVar(value="2.0")
        ttk.Label(g, text="설계조위").grid(row=0, column=0, sticky="w")
        ttk.Entry(g, textvariable=self.tide, width=10).grid(row=0, column=1)

        self.dyn = ttk.Frame(self.left); self.dyn.pack(fill="x")
        ttk.Button(self.left, text="계산", command=self.run).pack(fill="x", pady=8)
        self.txt = tk.Text(right, wrap="word", font=("Consolas", 11)); self.txt.pack(fill="both", expand=True)
        self.build()

    def build(self):
        for w in self.dyn.winfo_children():
            w.destroy()
        t = TYPES[self.tsel.get()]
        self.vars, self.fvars = {}, {}
        g = ttk.LabelFrame(self.dyn, text="표고·제원", padding=6); g.pack(fill="x", pady=3)
        for i, (k, l, d) in enumerate(t["inputs"]):
            ttk.Label(g, text=l).grid(row=i, column=0, sticky="w")
            self.vars[k] = tk.StringVar(value=d)
            ttk.Entry(g, textvariable=self.vars[k], width=10).grid(row=i, column=1)
        g = ttk.LabelFrame(self.dyn, text="계산식 (수정 가능)", padding=6); g.pack(fill="x", pady=3)
        for i, (k, l, d) in enumerate(t["formulas"]):
            ttk.Label(g, text=l).grid(row=i, column=0, sticky="w")
            self.fvars[k] = tk.StringVar(value=d)
            ttk.Entry(g, textvariable=self.fvars[k], width=40).grid(row=i, column=1)

    def run(self):
        self.txt.delete("1.0", "end")
        try:
            v = {k: float(x.get()) for k, x in self.vars.items()}
            forms = {k: x.get() for k, x in self.fvars.items()}
            Hs, Ts, tide = float(self.Hs.get()), float(self.Ts.get()), float(self.tide.get())
            r = calculate(self.tsel.get(), v, tide, Hs, Ts, forms)
        except Exception as e:
            messagebox.showerror("오류", str(e)); return
        L = [f"구조물 : {self.tsel.get()}", f"설계조위 : DL {tide:+.2f} m", "",
             f"수심 h        = {r['h']:.2f} m", f"파장 L        = {r['L']:.2f} m",
             f"파형경사 Hs/L = {r['s']:.4f}", f"여유고 Rc     = {r['Rc']:+.2f} m",
             f"마루수심 Dc   = {r['Dc']:+.2f} m", ""]
        L += [f"{k:<13} = {x:.4f}" for k, x in r["inter"].items() if k != "Kt"]
        L += [f"전달율 Kt     = {r['Kt']:.4f}", f"전달파고 Ht   = {r['Ht']:.3f} m",
              f"전달파 주기   ≒ {r['Tt']:.1f} s (입사주기의 50~80%, 65% 적용)", ""]
        L += ["※ " + w for w in r["warn"]]
        self.txt.insert("end", "\n".join(L))


if __name__ == "__main__":
    App().mainloop()