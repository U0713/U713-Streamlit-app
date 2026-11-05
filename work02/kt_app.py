# -*- coding: utf-8 -*-
"""파고 전달율(K_T)·전달파고(H_T) 계산 웹앱 | KDS 64 10 07 (2026) 4.4.12
실행:  pip install -r requirements.txt   →   streamlit run kt_app.py
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import kt_core as core

st.set_page_config(page_title="파고 전달율 계산", page_icon="🌊", layout="wide")

CSS = """
<style>
.block-container{padding-top:2.4rem;max-width:1250px}
.sec-title{border-left:6px solid #5b5fc7;padding:6px 14px;font-size:1.85rem;font-weight:700;margin:6px 0 14px;
 background:linear-gradient(90deg,rgba(91,95,199,.22),transparent)}
.sub-title{border-left:6px solid #5b5fc7;padding:2px 12px;font-size:1.35rem;font-weight:700;margin:26px 0 10px}
.banner{border-radius:12px;border:1px solid #2f4fa8;margin-bottom:22px;overflow:hidden;
 background:linear-gradient(135deg,#1c2540,#1a3478);padding-bottom:14px}
.bn-head{background:linear-gradient(90deg,#1d4ed8,#2f6df0);color:#fff;padding:10px 16px;font-weight:700}
.bn-head span{font-weight:500;font-size:.82rem;margin-left:10px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:16px 16px 4px}
.card{background:#111827;border-radius:10px;padding:14px 16px;border-top:3px solid var(--c);color:#e5e7eb;min-height:128px}
.ct{font-weight:700;font-size:.9rem}.cv{font-size:2rem;font-weight:800;color:var(--c);margin:6px 0 2px}
.cv small{font-size:1rem}.cs{font-size:.72rem;color:#9ca3af}
.pill{display:inline-block;margin-top:8px;padding:3px 12px;border-radius:14px;background:var(--c);color:#fff;font-size:.72rem;font-weight:700}
.tbl{width:100%;border-collapse:collapse;font-size:.84rem;margin:6px 0 18px}
.tbl th{background:#1e4fa3;color:#fff;padding:8px;border:1px solid rgba(128,128,128,.4);text-align:center}
.tbl td{padding:7px 9px;border:1px solid rgba(128,128,128,.35);text-align:center}
.tbl tr:nth-child(even) td{background:rgba(128,128,128,.08)}
.tbl td.k{font-weight:600}
.ok{color:#22c55e;font-weight:700}.ng{color:#ef4444;font-weight:700}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

DEFAULTS = dict(struct=core.STRUCTS[0], Hs=3.0, Ts=10.0, tide=0.0, bed=-15.0, crest=3.0, mound=-10.0,
                W=8.0, V=25.0, sub=core.SUBS[0], prj="", author="", reviewer="", memo="")
SAVE_KEYS = list(DEFAULTS)
# 화면에서 사라진 위젯(예: 구조물 형식 변경 시 근고부 상단고)의 값이 초기화되지 않도록 별도 저장소에 보관
_store = st.session_state.setdefault("_store", dict(DEFAULTS))
for k in SAVE_KEYS:
    if k not in st.session_state:
        st.session_state[k] = _store[k]


def apply_upload():
    f = st.session_state.get("upfile")
    if f is None:
        return
    try:
        data = json.load(f)
    except Exception:
        st.session_state["up_msg"] = "JSON 파일을 읽을 수 없습니다."
        return
    for k in SAVE_KEYS:
        if k in data:
            if k == "struct" and data[k] not in core.STRUCTS:
                continue
            if k == "sub" and data[k] not in core.SUBS:
                continue
            st.session_state[k] = data[k]
    st.session_state["up_msg"] = "입력값을 불러왔습니다."


def num(label, key, step=0.5, fmt="%.2f"):
    return st.number_input(label, step=step, format=fmt, key=key)


# ------------------------------------------------------------------ 사이드바(입력)
with st.sidebar:
    st.markdown("## 📥 입력 조건")
    struct = st.radio("① 구조물 형식", core.STRUCTS, key="struct")

    with st.expander("② 설계파 (구조물 위치 입사파)", expanded=True):
        c1, c2 = st.columns(2)
        with c1: num("유의파고 H₁/₃ (m)", "Hs")
        with c2: num("유의주기 T₁/₃ (s)", "Ts")

    with st.expander("③ 조위·표고 (DL.m)", expanded=True):
        c1, c2 = st.columns(2)
        with c1: num("설계조위 WL", "tide")
        with c2: num("전면 해저고", "bed")
        is_hy, is_ttp = struct == core.STRUCTS[0], struct == core.STRUCTS[1]
        c3, c4 = st.columns(2)
        with c3:
            num("직립부 마루고" if is_hy else ("상치콘크리트 마루고" if is_ttp else "구조물 상단고"), "crest")
        with c4:
            if is_hy:
                num("근고부(마운드) 상단고", "mound")
        h_, R_ = st.session_state["tide"] - st.session_state["bed"], st.session_state["crest"] - st.session_state["tide"]
        if is_hy:
            d_ = st.session_state["tide"] - st.session_state["mound"]
            st.caption(f"→ 수심 h = {h_:.2f} m · 여유고 R = {R_:.2f} m · 근고수심 d = {d_:.2f} m")
        else:
            st.caption(f"→ 수심 h = {h_:.2f} m · 여유고 R = {R_:.2f} m")

    if not is_hy:
        with st.expander("④ 구조물 제원", expanded=True):
            if is_ttp:
                c1, c2 = st.columns(2)
                with c1: num("전면 피복재 어깨폭 W (m)", "W")
                with c2: num("TTP 체적 V (m³)", "V")
            else:
                st.radio("수중구조물 유형", core.SUBS, key="sub", horizontal=True)
                num("마루폭 W (m)", "W")

    with st.expander("⑤ 조위별 일괄검토 (선택)"):
        use_batch = st.checkbox("일괄검토 사용", key="use_batch")
        batch_df = st.data_editor(
            pd.DataFrame({"조위명": ["조위명 1", "조위명 2", "조위명 3"], "설계조위": [2.0, 1.0, 0.0]}),
            num_rows="dynamic", use_container_width=True, key="batch_df", disabled=not use_batch)

    with st.expander("💾 입력 저장 / 불러오기"):
        payload = json.dumps({k: st.session_state[k] for k in SAVE_KEYS}, ensure_ascii=False, indent=2)
        st.download_button("입력값 저장 (JSON)", payload, "kt_input.json", "application/json", use_container_width=True)
        st.file_uploader("불러올 JSON", type="json", key="upfile")
        st.button("불러오기 적용", on_click=apply_upload, use_container_width=True)
        if st.session_state.get("up_msg"):
            st.caption(st.session_state.pop("up_msg"))

    with st.expander("🧑‍💼 매니저 관리"):
        st.text_input("프로젝트명", key="prj")
        st.text_input("작성자", key="author")
        st.text_input("검토자", key="reviewer")
        st.text_area("메모", key="memo", height=70)

    with st.expander("🧮 계산 정보"):
        st.markdown("- 파장 L: 선형 분산관계식 반복법 (수심 h, 유의주기 T₁/₃)\n- 전달파 주기: 입사주기의 50~80 %\n"
                    "- 조위 변화는 h, R(또는 R_C), d에 반영\n- 식 계수는 기준서 참고식 값을 그대로 사용")
    with st.expander("📐 적용 기준 (KDS 1종)"):
        st.markdown("**KDS 64 10 07 : 2026 설계조건 4.4.12 전달파고**\n- 참고식 (4.4-83) 합성\n"
                    "- (4.4-86) 직립혼성제(무공)\n- (4.4-84)~(4.4-85) TTP 피복 경사제\n"
                    "- (4.4-87)~(4.4-89) 수중구조물(투과형·경사형·불투과형)")

# ------------------------------------------------------------------ 계산
S = st.session_state
for k in SAVE_KEYS:
    if k in S:
        _store[k] = S[k]
args = dict(struct=struct, Hs=S["Hs"], Ts=S["Ts"], bed=S["bed"], crest=S["crest"],
            mound=S["mound"] if is_hy else None, W=S["W"] if not is_hy else None,
            V=S["V"] if is_ttp else None, sub=S["sub"])
try:
    res = core.calc(tide=S["tide"], **args)
except (ValueError, ZeroDivisionError) as e:
    st.error(f"계산 불가: {e}")
    st.stop()


# ------------------------------------------------------------------ 표시 헬퍼
def table(headers, rows):
    h = "".join("<th>" + x + "</th>" for x in headers)
    out = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            cls = ' class="k"' if (i == 0 and len(headers) == 2) else ""
            tds.append("<td" + cls + ">" + str(c) + "</td>")
        out.append("<tr>" + "".join(tds) + "</tr>")
    return '<table class="tbl"><tr>' + h + "</tr>" + "".join(out) + "</table>"


def badge(ok):
    return '<span class="ok">✅ 만족</span>' if ok else '<span class="ng">⚠️ 벗어남</span>'


def check_table(r):
    rows = [(c["name"], f'{c["val"]:.4f}', c["rng"] + (f' <small>({c["note"]})</small>' if c["note"] else ""),
             badge(c["ok"])) for c in r["checks"]]
    return table(["항목", "값", "적용범위", "판정"], rows)


def report_html(r):
    steps = "".join(f"<h4>{t}</h4><p>{n}</p>" for t, _, n in r["steps"])
    info = f'{S["prj"] or "-"} / 작성 {S["author"] or "-"} / 검토 {S["reviewer"] or "-"} / {dt.date.today()}'
    return ("<html><head><meta charset='utf-8'><style>body{font-family:'Malgun Gothic',sans-serif;margin:30px}"
            "table{border-collapse:collapse;width:100%}th{background:#1e4fa3;color:#fff}th,td{border:1px solid #999;padding:6px;"
            "text-align:center;font-size:13px}h1{border-left:6px solid #5b5fc7;padding-left:10px}</style></head><body>"
            f"<h1>파고 전달율 검토서</h1><p>{info}</p><p>근거: KDS 64 10 07 : 2026 4.4.12</p>"
            f"<h3>1. 결과</h3>{table(['항목', '값'], r['table'])}<h3>2. 적용범위 검토</h3>{check_table(r)}"
            f"<h3>3. 계산 과정</h3>{steps}<p>{S['memo']}</p></body></html>")


# ------------------------------------------------------------------ 본문
tabs = st.tabs(["📊 결과 요약", "📝 상세 풀이", "📚 개념·참고", "🖨️ 보고서 출력"])

with tabs[0]:
    st.markdown('<div class="sec-title">📊 결과 요약</div>', unsafe_allow_html=True)
    ok = res["all_ok"]
    note = "하한값 0.06 적용" if res["floor"] else "산정식 값 그대로 적용"
    cards = (
        f'<div class="card" style="--c:#8b8cf6"><div class="ct">📉 파고 전달율 K<sub>T</sub></div>'
        f'<div class="cv">{res["Kt"]:.3f}</div><div class="cs">{note}</div></div>'
        f'<div class="card" style="--c:#f43f5e"><div class="ct">🌊 전달파고 H<sub>T</sub></div>'
        f'<div class="cv">{res["Ht"]:.2f} <small>m</small></div>'
        f'<div class="cs">H<sub>T</sub> = K<sub>T</sub> × H = {res["Kt"]:.3f} × {res["Hs"]:.2f}</div>'
        f'<span class="pill">H<sub>T</sub> = {res["Ht"]:.2f} m</span></div>'
        f'<div class="card" style="--c:#38bdf8"><div class="ct">⏱️ 전달파 주기 T<sub>T</sub></div>'
        f'<div class="cv">{res["Tmin"]:.1f}~{res["Tmax"]:.1f}<small> s</small></div><div class="cs">입사주기의 50~80 %</div></div>'
        f'<div class="card" style="--c:{"#22c55e" if ok else "#f59e0b"}"><div class="ct">✅ 적용범위 검토</div>'
        f'<div class="cv">{"만족" if ok else "확인 필요"}</div><div class="cs">검토 {len(res["checks"])}개 항목</div>'
        f'<span class="pill">{"O.K" if ok else "주의"}</span></div>')
    st.markdown(f'<div class="banner"><div class="bn-head">📌 설계 한눈에 보기 <span>{res["struct"]}{res["Tsub"]} · '
                f'입사파고 {res["Hs"]:.2f} m</span></div><div class="cards">{cards}</div></div>', unsafe_allow_html=True)
    for w in res["warn"]:
        st.warning(w)
    st.markdown(table(["항목", "값"], res["table"]), unsafe_allow_html=True)
    st.markdown('<div class="sub-title">■ 적용범위 검토</div>', unsafe_allow_html=True)
    st.markdown(check_table(res), unsafe_allow_html=True)

    if use_batch:
        st.markdown('<div class="sub-title">■ 조위별 일괄검토</div>', unsafe_allow_html=True)
        rows = []
        for _, row in batch_df.dropna().iterrows():
            try:
                rr = core.calc(tide=float(row["설계조위"]), **args)
                nng = sum(not c["ok"] for c in rr["checks"])
                rows.append((row["조위명"], f'{rr["tide"]:+.2f}', f'{rr["h"]:.2f}', f'{rr["Rc"]:.2f}',
                             f'{rr["s"]:.4f}', f'{rr["Kt"]:.3f}', f'{rr["Ht"]:.3f}',
                             badge(True) if nng == 0 else f'<span class="ng">⚠️ {nng}항목 벗어남</span>'))
            except (ValueError, ZeroDivisionError) as e:
                rows.append((row["조위명"], f'{row["설계조위"]}', "-", "-", "-", "-", "-", f'<span class="ng">{e}</span>'))
        st.markdown(table(["조위명", "설계조위(DL m)", "h (m)", "R (m)", "s", "K<sub>T</sub>", "H<sub>T</sub> (m)", "적용범위"], rows),
                    unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="sec-title">📝 상세 풀이</div>', unsafe_allow_html=True)
    for title, latex, numeric in res["steps"]:
        st.markdown(f"**{title}**")
        st.latex(latex)
        st.code(numeric, language=None)

with tabs[2]:
    st.markdown('<div class="sec-title">📚 개념·참고</div>', unsafe_allow_html=True)
    st.markdown("""
**파고 전달율 K_T** = 전달파고 H_T / 입사파고 H_I. 월파에 의한 성분(K_TO)과 구조물 투과에 의한 성분(K_TT)을
에너지 합성하여 구합니다 (참고식 4.4-83).

| 기호 | 의미 |
|---|---|
| H₁/₃, T₁/₃ | 구조물 위치에서의 입사 유의파고·유의주기 |
| L₁/₃, s | 수심 h에서 유의주기에 대응하는 파장, 파형경사 H₁/₃/L₁/₃ |
| R | 여유고 (마루높이 − 설계조위) |
| d | 근고부(마운드) 상단 수심 (설계조위 − 근고부 상단고) |
| R_C | 수중구조물의 마루수심 (설계조위 − 구조물 상단고) |
| W | TTP 경사제의 전면 피복재 어깨폭 / 수중구조물 마루폭 |
| D_n | TTP 공칭길이 = V^(1/3) |

**적용 시 유의사항**
- 모든 식은 수리모형실험에 기초한 경험식이므로 적용범위를 벗어나면 수리모형실험으로 확인합니다.
- 식 4.4-84는 TTP 2층 정적피복, 직각입사, 전면 해저경사 1/50 조건의 식입니다.
- 식 4.4-87~89는 2차원 실험 결과로 구조물 길이·개구폭·입사각의 영향은 반영하지 못합니다.
- 조위가 높아 R이 작아지면 K_T가 커집니다. 조위별 일괄검토로 가장 불리한 조위를 확인하세요.
""")

with tabs[3]:
    st.markdown('<div class="sec-title">🖨️ 보고서 출력</div>', unsafe_allow_html=True)
    html = report_html(res)
    c1, c2 = st.columns(2)
    c1.download_button("📄 검토서 다운로드 (HTML → 인쇄/PDF)", html, "kt_report.html", "text/html", use_container_width=True)
    csv = pd.DataFrame([(a.replace("<sub>", "").replace("</sub>", ""), b.replace("<sub>", "").replace("</sub>", ""))
                        for a, b in res["table"]], columns=["항목", "값"]).to_csv(index=False).encode("utf-8-sig")
    c2.download_button("📊 결과표 다운로드 (CSV)", csv, "kt_result.csv", "text/csv", use_container_width=True)
    components.html(html, height=620, scrolling=True)
