# -*- coding: utf-8 -*-
"""KDS 64 10 07 (2026) 4.4.12 파고 전달율 계산 코어 (화면과 분리된 순수 계산 모듈)
 ① 직립혼성제(무공)  : 참고식 4.4-83, 4.4-86
 ② TTP 피복 경사제   : 참고식 4.4-84, 4.4-85
 ③ 수중구조물        : 참고식 4.4-87(투과형) / 4.4-88(경사형) / 4.4-89(불투과형)
"""
import math

G = 9.80665
STRUCTS = ["직립혼성제 (무공)", "TTP 피복 경사제", "수중구조물 (잠제·인공리프)"]
SUBS = ["투과형", "경사형", "불투과형"]
# 수중구조물 계수 : (c1 exp(Rc/h), c2 exp(Rc/Hs), c3 ln(Hs/L), c4 ln(W/L), c5, 식번호, s범위, W/L범위)
SUB_COEF = {
    "투과형":   (0.380, 0.095, 0.072, -0.188, 0.013, "4.4-87", (0.01, 0.06),  (0.04, 1.5)),
    "경사형":   (0.278, 0.146, 0.075, -0.205, -0.015, "4.4-88", (0.01, 0.065), (0.05, 1.5)),
    "불투과형": (0.483, 0.093, 0.019, -0.157, -0.376, "4.4-89", (0.01, 0.065), (0.05, 1.5)),
}


def wavelength(T, h):
    """분산관계식 (참고식 4.4-2) 반복법"""
    L0 = G * T ** 2 / (2 * math.pi)
    L = L0
    for _ in range(500):
        Ln = L0 * math.tanh(2 * math.pi * h / L)
        if abs(Ln - L) < 1e-10:
            break
        L = Ln
    return L


def calc(struct, tide, Hs, Ts, bed, crest, mound=None, W=None, V=None, sub="투과형"):
    h = tide - bed
    if h <= 0:
        raise ValueError("설계조위가 전면 해저고보다 낮아 수심이 0 이하입니다.")
    if Hs <= 0 or Ts <= 0:
        raise ValueError("유의파고와 유의주기는 0보다 커야 합니다.")
    L = wavelength(Ts, h)
    s = Hs / L
    Rc = crest - tide              # 여유고 (정수면 위 +)
    Dc = -Rc                       # 마루수심 (정수면 아래 +)
    o = dict(struct=struct, tide=tide, bed=bed, crest=crest, Hs=Hs, Ts=Ts, h=h, L=L, s=s,
             Rc=Rc, Dc=Dc, checks=[], steps=[], warn=[], floor=False, inter={})

    def chk(name, val, lo, hi, note=""):
        o["checks"].append(dict(name=name, val=val, rng=f"{lo} ~ {hi}", ok=lo <= val <= hi, note=note))

    sub_txt = ""
    if struct == STRUCTS[0]:
        if mound is None:
            raise ValueError("근고부 상단고를 입력하세요.")
        d = tide - mound
        if d < 0:
            raise ValueError("근고부 상단고가 설계조위보다 높습니다 (d < 0).")
        if d > h:
            raise ValueError("근고부 상단고가 전면 해저고보다 낮습니다 (d > h).")
        if Rc < 0:
            raise ValueError("설계조위가 직립부 마루높이보다 높아(R < 0) 식 4.4-86을 적용할 수 없습니다.")
        Kto = 3.17 * math.exp(-1.67 * (Rc / Hs) ** 0.36 * s ** (-0.24))
        Ktt = math.sqrt(0.014 * (1 - d / h) ** 2)
        Kt = math.sqrt(Kto ** 2 + Ktt ** 2)
        o.update(d=d, mound=mound, Kto=Kto, Ktt=Ktt, inter=dict(Kto=Kto, Ktt=Ktt))
        chk("R/H₁/₃", Rc / Hs, 0.3, 2.6); chk("s = H₁/₃/L₁/₃", s, 0.02, 0.05); chk("d/h", d / h, 0.5, 1.0)
        o["steps"] = [
            ("① 수심·파장·파형경사", r"L=\frac{gT^2}{2\pi}\tanh\frac{2\pi h}{L},\quad s=\frac{H_{1/3}}{L_{1/3}}",
             f"h = {tide:.2f} − ({bed:.2f}) = {h:.2f} m,  L = {L:.2f} m,  s = {Hs:.2f}/{L:.2f} = {s:.4f}"),
            ("② 월파에 의한 전달율 (4.4-86 1항)",
             r"K_{TO}=3.17\exp\left[-1.67\left(\frac{R}{H_{1/3}}\right)^{0.36}s^{-0.24}\right]",
             f"R = {crest:.2f} − ({tide:.2f}) = {Rc:.2f} m  →  K_TO = 3.17·exp[−1.67·({Rc:.2f}/{Hs:.2f})^0.36·{s:.4f}^−0.24] = {Kto:.4f}"),
            ("③ 투과에 의한 전달율 (4.4-86 2항)", r"K_{TT}=\sqrt{0.014\left(1-\frac{d}{h}\right)^2}",
             f"d = {tide:.2f} − ({mound:.2f}) = {d:.2f} m  →  K_TT = √[0.014·(1 − {d:.2f}/{h:.2f})²] = {Ktt:.4f}"),
            ("④ 합성 (4.4-83)", r"K_T=\sqrt{K_{TO}^2+K_{TT}^2}=\frac{H_T}{H_I}",
             f"K_T = √({Kto:.4f}² + {Ktt:.4f}²) = {Kt:.4f},  H_T = K_T·H_I = {Kt:.4f}×{Hs:.2f} = {Kt*Hs:.3f} m"),
        ]
        rowsx = [("여유고 R / 근고수심 d", f"{Rc:.2f} m / {d:.2f} m"),
                 ("K<sub>TO</sub>(월파) / K<sub>TT</sub>(투과)", f"{Kto:.4f} / {Ktt:.4f}")]
    elif struct == STRUCTS[1]:
        if not V or V <= 0:
            raise ValueError("TTP 체적 V는 0보다 커야 합니다.")
        W = W or 0.0
        Dn = V ** (1 / 3)
        a_s = 5 * s + 0.233
        a_row = 0.0143 * (W / Dn) - 0.0331
        raw = a_s - 0.31 * (Rc / Hs) - a_row
        Kt = max(raw, 0.06)
        o["floor"] = raw < 0.06
        o.update(W=W, V=V, Dn=Dn, inter=dict(a_s=a_s, a_row=a_row, raw=raw))
        chk("s = H₁/₃/L₁/₃", s, 0.015, 0.044, "기호 순서 추정"); chk("R/H₁/₃", Rc / Hs, 0.6, 2.0, "기호 순서 추정")
        chk("W/Dn", W / Dn, 2.32, 5.12, "기호 순서 추정")
        if Rc <= 0:
            o["warn"].append("설계조위가 상치콘크리트 마루높이 이상입니다.")
        o["warn"].append("식 4.4-84는 TTP 2층 정적피복·직각입사·전면 해저경사 1/50 실험식입니다.")
        o["steps"] = [
            ("① 수심·파장·파형경사", r"L=\frac{gT^2}{2\pi}\tanh\frac{2\pi h}{L},\quad s=\frac{H_{1/3}}{L_{1/3}}",
             f"h = {h:.2f} m,  L = {L:.2f} m,  s = {s:.4f},  R = {Rc:.2f} m,  D_n = V^(1/3) = {V:.2f}^(1/3) = {Dn:.3f} m"),
            ("② 파형경사 항 (4.4-85)", r"\alpha_s=5s+0.233", f"α_s = 5×{s:.4f} + 0.233 = {a_s:.4f}"),
            ("③ 어깨폭 항 (4.4-85)", r"\alpha_{row}=0.0143\frac{W}{D_n}-0.0331",
             f"α_row = 0.0143×({W:.2f}/{Dn:.3f}) − 0.0331 = {a_row:.4f}"),
            ("④ 전달율 (4.4-84)", r"K_T=\alpha_s-0.31\frac{R}{H_{1/3}}-\alpha_{row},\quad (K_T)_{min}=0.06",
             f"K_T = {a_s:.4f} − 0.31×({Rc:.2f}/{Hs:.2f}) − ({a_row:.4f}) = {raw:.4f}"
             + (f"  →  하한 0.06 적용" if o["floor"] else "") + f",  H_T = {Kt:.4f}×{Hs:.2f} = {Kt*Hs:.3f} m"),
        ]
        rowsx = [("여유고 R / 어깨폭 W / D<sub>n</sub>", f"{Rc:.2f} m / {W:.2f} m / {Dn:.2f} m"),
                 ("α<sub>s</sub> / α<sub>row</sub>", f"{a_s:.4f} / {a_row:.4f}")]
    else:
        if not W or W <= 0:
            raise ValueError("마루폭 W는 0보다 커야 합니다.")
        c1, c2, c3, c4, c5, eq, srng, wrng = SUB_COEF[sub]
        t = [c1 * math.exp(Dc / h), c2 * math.exp(Dc / Hs), c3 * math.log(s), c4 * math.log(W / L), c5]
        Kt = sum(t)
        sub_txt = f" · {sub}"
        o.update(W=W, sub=sub, eq=eq, inter={f"항{i+1}": x for i, x in enumerate(t)})
        chk("s = H₁/₃/L₁/₃", s, *srng); chk("W/L₁/₃", W / L, *wrng)
        if Dc <= 0:
            o["warn"].append("구조물 상단이 정수면 이상입니다 (수중구조물 조건 아님).")
        if not 0 <= Kt <= 1:
            o["warn"].append(f"산정된 K_T = {Kt:.3f} 가 0~1 범위를 벗어났습니다. 적용범위를 확인하세요.")
        o["warn"].append("식 4.4-87~89는 2차원 수리실험식으로 구조물 길이·개구폭·입사각 영향은 포함하지 않습니다.")
        o["steps"] = [
            ("① 수심·파장·파형경사", r"L=\frac{gT^2}{2\pi}\tanh\frac{2\pi h}{L},\quad s=\frac{H_{1/3}}{L_{1/3}}",
             f"h = {h:.2f} m,  L = {L:.2f} m,  s = {s:.4f},  R_C(마루수심) = {tide:.2f} − ({crest:.2f}) = {Dc:.2f} m"),
            (f"② 전달율 (참고식 {eq}, {sub})",
             rf"K_T={c1:.3f}\exp\left(\frac{{R_C}}{{h}}\right){c2:+.3f}\exp\left(\frac{{R_C}}{{H_{{1/3}}}}\right)"
             rf"{c3:+.3f}\ln\left(\frac{{H_{{1/3}}}}{{L_{{1/3}}}}\right){c4:+.3f}\ln\left(\frac{{W}}{{L_{{1/3}}}}\right){c5:+.3f}",
             f"항별 값 = {t[0]:.4f}, {t[1]:.4f}, {t[2]:+.4f}, {t[3]:+.4f}, {t[4]:+.4f}  →  K_T = {Kt:.4f},  H_T = {Kt:.4f}×{Hs:.2f} = {Kt*Hs:.3f} m"),
        ]
        rowsx = [("마루수심 R<sub>C</sub> / 마루폭 W", f"{Dc:.2f} m / {W:.2f} m"), ("산정식", f"참고식 ({eq}) · {sub}")]

    Ht = Kt * Hs
    o.update(Kt=Kt, Ht=Ht, Tmin=0.5 * Ts, Tmax=0.8 * Ts, Tsub=sub_txt)
    o["table"] = [
        ("구조물 형식", struct + sub_txt),
        ("입사파 H<sub>1/3</sub> / T<sub>1/3</sub>", f"{Hs:.2f} m / {Ts:.2f} s"),
        ("설계조위 / 해저고 / 수심 h", f"DL{tide:+.2f} / DL{bed:+.2f} / {h:.2f} m"),
        ("유의파 파장 L<sub>1/3</sub> / 파형경사 s", f"{L:.2f} m / {s:.4f}"),
    ] + rowsx + [("파고 전달율 K<sub>T</sub> (적용)", f"{Kt:.3f}"), ("전달파고 H<sub>T</sub>", f"{Ht:.3f} m")]
    o["all_ok"] = all(c["ok"] for c in o["checks"])
    return o


if __name__ == "__main__":
    r = calc(STRUCTS[0], 0.0, 3.0, 10.0, -15.0, 3.0, mound=-10.0)
    print(r["h"], r["L"], r["s"], r["Kto"], r["Ktt"], r["Kt"], r["Ht"])
