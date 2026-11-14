"""
SudokuX : CYBERPUNK TERMINAL EDITION
Run with: streamlit run app.py
"""
import json
from copy import deepcopy
from time import perf_counter

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------- DO NOT CHANGE IMPORTS ----------
from solver.backtracking import SudokuSolver
from solver.difficulty import analyze_difficulty
from experiments.benchmark import ALGORITHMS, run_once
from experiments.benchmark_puzzles import PUZZLES
# -----------------------------------------

st.set_page_config(
    page_title="SudokuX | NEURAL-NET",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 1. GLOBAL STYLES & CSS VARIABLES
# ==========================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&display=swap');

:root {
    /* Cyberpunk Palette */
    --bg: #05060d;
    --panel: #0a0a1a;
    --panel-border: rgba(0, 240, 255, 0.3);
    --cyan: #00f0ff;
    --magenta: #ff2a6d;
    --yellow: #f9f002;
    --green: #05ffa1;
    --text: #e0e0e0;
    --muted: #4b5563;
    --glow-strength: 0 0 10px;
}

/* Force Dark Mode & Fonts */
.stApp {
    background-color: var(--bg) !important;
    background-image: 
        linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
    background-size: 30px 30px;
    background-position: center center;
    color: var(--text) !important;
    font-family: 'Share Tech Mono', monospace;
}

/* CRT Scanlines & Vignette */
.stApp::after {
    content: ""; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    background-size: 100% 4px, 3px 100%;
    pointer-events: none; z-index: 9999;
}
.stApp::before {
    content: ""; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: radial-gradient(circle, transparent 50%, rgba(0,0,0,0.7) 100%);
    pointer-events: none; z-index: 9998;
}

/* Hide Defaults */
#MainMenu, header, footer {visibility: hidden; display: none;}

/* Typography & Headings */
h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    text-transform: uppercase;
    color: var(--cyan) !important;
    text-shadow: var(--glow-strength) var(--cyan);
    letter-spacing: 2px;
}
h1::before, h2::before, h3::before {
    content: "> "; color: var(--magenta);
}

/* HUD Cards (Containers & Expanders) */
[data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"],
div[data-testid="stExpander"] {
    background: var(--panel) !important;
    border: 1px solid var(--panel-border) !important;
    clip-path: polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px);
    padding: 10px;
    box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.05);
    position: relative;
    animation: bootUp 0.5s ease-out forwards;
}
[data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"]::before {
    content: "[ MODULE_ACTIVE ]"; position: absolute; top: -10px; right: 15px;
    background: var(--bg); color: var(--cyan); font-size: 10px; padding: 0 5px;
}

@keyframes bootUp {
    0% { opacity: 0.1; filter: contrast(300%) brightness(200%); }
    50% { opacity: 0.8; filter: contrast(100%) brightness(50%); }
    100% { opacity: 1; filter: none; }
}

/* Buttons */
div.stButton > button {
    font-family: 'Orbitron', sans-serif;
    text-transform: uppercase;
    background: transparent;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan);
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    border-radius: 0;
    transition: all 0.2s;
    box-shadow: 0 0 5px rgba(0, 240, 255, 0.3);
}
div.stButton > button:hover {
    background: rgba(0, 240, 255, 0.1);
    box-shadow: var(--glow-strength) var(--cyan), inset 0 0 10px var(--cyan);
}
div.stButton > button[kind="primary"] {
    border: 1px solid var(--magenta);
    color: var(--magenta) !important;
    background: rgba(255, 42, 109, 0.05);
    box-shadow: 0 0 10px rgba(255, 42, 109, 0.4);
}
div.stButton > button[kind="primary"]:hover {
    background: var(--magenta);
    color: #000 !important;
    box-shadow: 0 0 20px var(--magenta);
    animation: glitch-flicker 0.2s infinite;
}

@keyframes glitch-flicker {
    0% { transform: translate(0) }
    20% { transform: translate(-2px, 1px) }
    40% { transform: translate(2px, -1px) }
    60% { transform: translate(-1px, 2px) }
    80% { transform: translate(1px, -2px) }
    100% { transform: translate(0) }
}

/* Data Editor / Terminal Grid */
div[data-testid="stDataEditor"] {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(10, 10, 26, 0.9) !important;
    border-top: 2px solid var(--cyan);
    padding: 10px;
}
[data-testid="stMetricValue"] {
    color: var(--cyan) !important;
    font-family: 'Share Tech Mono', monospace;
    text-shadow: 0 0 5px var(--cyan);
}

/* Alerts / Logs */
div[data-testid="stAlert"] {
    background: var(--panel);
    border-radius: 0;
    border-left: 4px solid var(--cyan);
    font-family: 'Share Tech Mono', monospace;
    color: var(--text);
}
div[data-testid="stAlert"]:has(svg[data-testid="stIconSuccess"]) { border-left-color: var(--green); color: var(--green); }
div[data-testid="stAlert"]:has(svg[data-testid="stIconError"]) { border-left-color: var(--magenta); color: var(--magenta); }
div[data-testid="stAlert"]:has(svg[data-testid="stIconWarning"]) { border-left-color: var(--yellow); color: var(--yellow); }

/* Solution Board (Hologram) */
.cyber-grid-container {
    display: grid; grid-template-columns: repeat(9, 1fr); gap: 2px;
    background: var(--cyan); border: 2px solid var(--cyan);
    padding: 2px; max-width: 450px; margin: 2rem auto;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
    position: relative; overflow: hidden;
}
.cyber-grid-container::after {
    content: ""; position: absolute; top: -100%; left: 0; width: 100%; height: 20%;
    background: linear-gradient(transparent, rgba(0, 240, 255, 0.8), transparent);
    animation: scanSweep 3s linear infinite; pointer-events: none;
}
@keyframes scanSweep { 0% { top: -20%; } 100% { top: 120%; } }

.cyber-cell {
    background: var(--bg); aspect-ratio: 1;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; color: var(--muted);
    position: relative; animation: decrypt 0.3s forwards;
}
.cyber-cell.given { color: var(--yellow); text-shadow: 0 0 8px var(--yellow); font-weight: bold; }
.cyber-cell.solved { color: var(--green); text-shadow: 0 0 10px var(--green); font-weight: bold; }
.cyber-cell.thick-right { margin-right: 2px; }
.cyber-cell.thick-bottom { margin-bottom: 2px; }

@keyframes decrypt {
    0% { opacity: 0; transform: scale(0.8); color: var(--magenta); content: "0"; }
    100% { opacity: 1; transform: scale(1); }
}

/* Celebration Banners */
.access-granted {
    background: rgba(5, 255, 161, 0.1); border: 1px solid var(--green);
    color: var(--green); text-align: center; padding: 15px;
    font-family: 'Orbitron', sans-serif; font-size: 24px;
    box-shadow: inset 0 0 15px rgba(5, 255, 161, 0.2), 0 0 15px rgba(5, 255, 161, 0.4);
    animation: bootUp 0.5s ease-out; margin-bottom: 20px; text-transform: uppercase;
}
.access-denied {
    background: rgba(255, 42, 109, 0.1); border: 1px solid var(--magenta);
    color: var(--magenta); text-align: center; padding: 15px;
    font-family: 'Orbitron', sans-serif; font-size: 24px;
    box-shadow: inset 0 0 15px rgba(255, 42, 109, 0.2), 0 0 15px rgba(255, 42, 109, 0.4);
    animation: bootUp 0.5s ease-out; margin-bottom: 20px; text-transform: uppercase;
}

/* Scrollbar & Selection */
::-webkit-scrollbar { width: 8px; background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--cyan); border-radius: 0; }
::selection { background: var(--magenta); color: #fff; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# 2. HERO COMPONENT (MATRIX + GLITCH)
# ==========================================
HERO_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; overflow: hidden; background: transparent; font-family: 'Share Tech Mono', monospace; color: #00f0ff; }
  canvas { position: absolute; top: 0; left: 0; z-index: 1; opacity: 0.2; }
  .content { position: relative; z-index: 2; padding: 40px; display: flex; flex-direction: column; justify-content: center; height: 100vh; box-sizing: border-box; }
  .glitch-title { font-family: 'Orbitron', sans-serif; font-size: 5rem; font-weight: 900; margin: 0; color: #fff; text-shadow: 2px 0 #ff2a6d, -2px 0 #00f0ff; position: relative; }
  .glitch-title::before, .glitch-title::after { content: 'SUDOKUX'; position: absolute; top: 0; left: 0; background: transparent; color: #fff; }
  .glitch-title::before { left: 2px; text-shadow: -2px 0 #ff2a6d; clip-path: polygon(0 0, 100% 0, 100% 45%, 0 45%); animation: glitch-anim 2s infinite linear alternate-reverse; }
  .glitch-title::after { left: -2px; text-shadow: -2px 0 #00f0ff; clip-path: polygon(0 80%, 100% 20%, 100% 100%, 0 100%); animation: glitch-anim 3s infinite linear alternate-reverse; }
  .boot-seq { margin-top: 20px; font-size: 14px; opacity: 0.8; line-height: 1.5; }
  .cursor { display: inline-block; width: 10px; height: 1em; background: #05ffa1; animation: blink 1s step-end infinite; vertical-align: bottom; margin-left: 5px; }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes glitch-anim {
    0% { clip-path: polygon(0 2%, 100% 2%, 100% 5%, 0 5%); }
    20% { clip-path: polygon(0 15%, 100% 15%, 100% 15%, 0 15%); }
    40% { clip-path: polygon(0 10%, 100% 10%, 100% 20%, 0 20%); }
    60% { clip-path: polygon(0 1%, 100% 1%, 100% 2%, 0 2%); }
    80% { clip-path: polygon(0 33%, 100% 33%, 100% 33%, 0 33%); }
    100% { clip-path: polygon(0 44%, 100% 44%, 100% 44%, 0 44%); }
  }
</style>
</head>
<body>
  <canvas id="matrix"></canvas>
  <div class="content">
    <h1 class="glitch-title">SUDOKUX</h1>
    <div class="boot-seq">
      > ESTABLISHING SECURE CONNECTION... OK<br>
      > INITIALIZING CSP ENGINE... OK<br>
      > LOADING NEURAL TRACE MODULE... <span style="color:#05ffa1">READY</span><br>
      > AWAITING INPUT MATRIX<span class="cursor"></span>
    </div>
  </div>
  <script>
    const canvas = document.getElementById('matrix');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth; canvas.height = window.innerHeight;
    const chars = '01ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const drops = [];
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    for(let i=0; i<columns; i++) drops[i] = 1;
    function draw() {
      ctx.fillStyle = 'rgba(5, 6, 13, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#00f0ff';
      ctx.font = fontSize + 'px Share Tech Mono';
      for(let i=0; i<drops.length; i++) {
        const text = chars.charAt(Math.floor(Math.random() * chars.length));
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    }
    setInterval(draw, 33);
  </script>
</body>
</html>
"""
components.html(HERO_HTML, height=250)


# ==========================================
# 3. SESSION STATE & HELPERS
# ==========================================
if "board_revision" not in st.session_state:
    st.session_state.board_revision = 0
if "board_data" not in st.session_state:
    st.session_state.board_data = deepcopy(PUZZLES["Puzzle_1"])
if "solve_result" not in st.session_state:
    st.session_state.solve_result = None
if "difficulty_result" not in st.session_state:
    st.session_state.difficulty_result = None
if "battle_result" not in st.session_state:
    st.session_state.battle_result = None
if "trace_events" not in st.session_state:
    st.session_state.trace_events = []
if "trace_index" not in st.session_state:
    st.session_state.trace_index = 0

def invalidate_results():
    st.session_state.solve_result = None
    st.session_state.difficulty_result = None
    st.session_state.battle_result = None
    st.session_state.trace_events = []
    st.session_state.trace_index = 0

def load_board(board):
    st.session_state.board_data = deepcopy(board)
    st.session_state.board_revision += 1
    invalidate_results()

def render_board(board, title=None, original_board=None):
    if not board:
        return
    if title:
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    html = '<div class="cyber-grid-container">'
    delay = 0.0
    for r in range(min(9, len(board))):
        for c in range(min(9, len(board[r]))):
            val = board[r][c]
            val_str = str(val) if val != 0 else ""
            classes = ["cyber-cell"]
            if c in (2, 5): classes.append("thick-right")
            if r in (2, 5): classes.append("thick-bottom")
            if original_board and r < len(original_board) and c < len(original_board[r]) and original_board[r][c] != 0:
                classes.append("given")
            elif val != 0:
                classes.append("solved")
            html += f'<div class="{" ".join(classes)}" style="animation-delay: {delay:.3f}s;">{val_str}</div>'
            delay += 0.015
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def metrics_row(metrics):
    if not metrics:
        return
    a, b, c, d = st.columns(4)
    a.metric("NODES", metrics.get("nodes_explored", 0))
    b.metric("BACKTRACKS", metrics.get("backtracks", 0))
    c.metric("CHECKS", metrics.get("constraint_checks", 0))
    time_val = metrics.get('time_ms', 0)
    d.metric("TIME_MS", f"{time_val:.3f}" if isinstance(time_val, (int, float)) else str(time_val))


# ==========================================
# 4. MAIN TERMINAL LAYOUT
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)

sample_labels = {
    "SECTOR_1 [EASY]": "Puzzle_1",
    "SECTOR_2 [MED]": "Puzzle_2",
    "SECTOR_3 [HARD]": "Puzzle_3",
    "OMEGA_PROTOCOL [EXPERT]": "Puzzle_4",
}
top_left, top_mid, top_right = st.columns([2.1, 1, 1])
with top_left:
    selected_sample = st.selectbox("ARCHIVE_ACCESS", list(sample_labels.keys()), label_visibility="collapsed")
with top_mid:
    if st.button("LOAD_MATRIX", use_container_width=True):
        load_board(PUZZLES[sample_labels[selected_sample]])
        st.rerun()
with top_right:
    if st.button("PURGE_GRID", use_container_width=True):
        load_board([[0] * 9 for _ in range(9)])
        st.rerun()

st.markdown("<h2>// INPUT_MATRIX</h2>", unsafe_allow_html=True)

revision = st.session_state.board_revision
column_names = [f"C{i}" for i in range(1, 10)]
grid_df = pd.DataFrame(st.session_state.board_data, columns=column_names)

def cyber_grid_style(df):
    styles = pd.DataFrame("", index=range(9), columns=column_names)
    for r in range(9):
        for c in range(9):
            val = df.iat[r, c]
            css = [
                "text-align: center", "font-size: 20px", "font-weight: bold",
                "color: var(--text)", "background-color: transparent",
                "border: 1px solid rgba(0, 240, 255, 0.2)"
            ]
            if val == 0: css.append("color: transparent")
            thick = "3px solid var(--cyan)"
            if c in (2, 5): css.append(f"border-right: {thick}")
            if r in (2, 5): css.append(f"border-bottom: {thick}")
            styles.iat[r, c] = ";".join(css)
    return styles

styled_grid = grid_df.style.apply(cyber_grid_style, axis=None)
column_config = { col: st.column_config.NumberColumn(min_value=0, max_value=9, step=1, format="%d", width="small") for col in column_names }

edited_grid = st.data_editor(
    styled_grid, key=f"grid_{revision}", column_config=column_config,
    hide_index=True, use_container_width=True, height=430
)

try:
    numeric_df = edited_grid[column_names].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
    board_input = numeric_df.clip(lower=0, upper=9).values.tolist()
    if len(board_input) == 9 and all(len(row) == 9 for row in board_input):
        if board_input != st.session_state.board_data:
            st.session_state.board_data = deepcopy(board_input)
            invalidate_results()
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)
opt1, opt2, opt3 = st.columns([1, 1, 1.35])
with opt1:
    difficulty_on = st.toggle("MODULE: THREAT_SCAN", value=False)
with opt2:
    analysis_on = st.toggle("MODULE: WARGAMES", value=False)
with opt3:
    strategy_names = {
        "PROTOCOL: AC3_MRV_DEG": "AC3 + MRV + Degree + FC",
        "PROTOCOL: FAST_BT_MRV": "BT + MRV",
        "PROTOCOL: BRUTE_FORCE": "Basic BT",
        "PROTOCOL: FULL_AI_SEQ": "Full AI (AC3 + MRV + Degree + LCV + FC)",
    }
    chosen_strategy = st.selectbox("ALGORITHM", list(strategy_names.keys()), label_visibility="collapsed")

action_col, reset_col = st.columns([2, 1])
with action_col:
    solve_clicked = st.button(">>> EXECUTE_SOLVE_SEQUENCE", type="primary", use_container_width=True)
with reset_col:
    if st.button("CLEAR_LOGS", use_container_width=True):
        invalidate_results()
        st.rerun()

if solve_clicked:
    config = ALGORITHMS.get(strategy_names.get(chosen_strategy, ""), {})
    try:
        solver = SudokuSolver(deepcopy(st.session_state.board_data), record_steps=True, **config)
        solved = solver.solve()
        st.session_state.solve_result = {
            "solved": solved,
            "solution": deepcopy(solver.board) if solved else None,
            "metrics": solver.get_metrics(),
            "errors": solver.validation_errors,
            "method": chosen_strategy,
        }
        st.session_state.trace_events = solver.events
        st.session_state.trace_index = 0
    except Exception as e:
        st.session_state.solve_result = {
            "solved": False,
            "solution": None,
            "metrics": {},
            "errors": [f"Execution error: {str(e)}"],
            "method": chosen_strategy,
        }
        st.session_state.trace_events = []
        st.session_state.trace_index = 0


# ==========================================
# 5. MODULE PANELS
# ==========================================
if difficulty_on:
    with st.container():
        st.markdown("<h3>THREAT_SCAN_RESULTS</h3>", unsafe_allow_html=True)
        try:
            result = analyze_difficulty(st.session_state.board_data)
            st.session_state.difficulty_result = result
            if not result.get("valid"):
                st.error("[ERR] MATRIX CORRUPTED.")
                for err in result.get("errors", []):
                    st.markdown(f"<div style='color:var(--magenta); font-family: monospace; margin: 4px 0 4px 10px;'>&gt; {err}</div>", unsafe_allow_html=True)
            elif not result.get("solvable"):
                st.warning("[WARN] NO SOLUTION VECTOR FOUND.")
            else:
                st.info(f"[INFO] CLASSIFICATION: {result.get('difficulty', 'UNKNOWN')}")
                x1, x2, x3, x4 = st.columns(4)
                x1.metric("VOID_CELLS", result.get("empty_cells", 0))
                x2.metric("ENTROPY", result.get("initial_candidate_count", 0))
                x3.metric("LOCKED_CELLS", result.get("initial_forced_cells", 0))
                x4.metric("COMPLEXITY", result.get("complexity_score", 0))
        except Exception as e:
            st.error(f"[ERR] THREAT SCAN FAILED: {str(e)}")

if st.session_state.solve_result:
    result = st.session_state.solve_result
    with st.container():
        if result.get("errors"):
            st.error("[ERR] INVALID INPUT DETECTED.")
            for err in result["errors"]:
                st.markdown(f"<div style='color:var(--magenta); font-family: monospace; margin: 4px 0 4px 10px;'>&gt; {err}</div>", unsafe_allow_html=True)
        elif result.get("solved"):
            st.markdown("<div class='access-granted'>ACCESS GRANTED // MATRIX DECRYPTED</div>", unsafe_allow_html=True)
            render_board(result["solution"], title="DECRYPTED_STATE", original_board=st.session_state.board_data)
            metrics_row(result["metrics"])
        else:
            st.markdown("<div class='access-denied'>ACCESS DENIED // KERNEL PANIC</div>", unsafe_allow_html=True)
            metrics_row(result["metrics"])

if analysis_on:
    with st.container():
        st.markdown("<h3>WARGAMES_BENCHMARK</h3>", unsafe_allow_html=True)
        run_count = st.select_slider("ITERATIONS", options=[1, 2, 3, 5], value=3)
        if st.button("INITIATE_BATTLE", use_container_width=True):
            probe = SudokuSolver(deepcopy(st.session_state.board_data))
            if probe.validation_errors:
                st.error("[ERR] CANNOT INITIATE BATTLE: MATRIX CORRUPTED.")
                for err in probe.validation_errors:
                    st.markdown(f"<div style='color:var(--magenta); font-family: monospace; margin: 4px 0 4px 10px;'>&gt; {err}</div>", unsafe_allow_html=True)
            else:
                try:
                    rows = []
                    progress = st.progress(0.0)
                    algorithms = list(ALGORITHMS.items())
                    for index, (name, config) in enumerate(algorithms):
                        runs = [run_once(st.session_state.board_data, config) for _ in range(run_count)]
                        first = runs[0]
                        rows.append({
                            "Protocol": name, "Status": "SUCCESS" if all(x["solved"] for x in runs) else "FAIL",
                            "Ping(ms)": round(sum(x["time_ms"] for x in runs) / run_count, 3),
                            "Nodes": first.get("nodes_explored", 0), "Backtracks": first.get("backtracks", 0),
                        })
                        progress.progress((index + 1) / len(algorithms))
                    st.session_state.battle_result = pd.DataFrame(rows)
                except Exception as e:
                    st.error(f"[ERR] BENCHMARK EXECUTION FAILED: {str(e)}")
        if st.session_state.battle_result is not None:
            st.dataframe(st.session_state.battle_result, hide_index=True, use_container_width=True)

if st.session_state.trace_events:
    with st.expander("NEURAL_TRACE // REPLAY"):
        events = st.session_state.trace_events
        st.caption(f"{len(events)} PACKET{'S' if len(events) != 1 else ''} LOGGED")
        if len(events) > 1:
            curr_idx = min(max(0, st.session_state.trace_index), len(events) - 1)
            selected_event = st.slider(
                "TIMELINE",
                min_value=1,
                max_value=len(events),
                value=curr_idx + 1,
            )
            st.session_state.trace_index = selected_event - 1
        else:
            st.session_state.trace_index = 0

        if 0 <= st.session_state.trace_index < len(events):
            event = events[st.session_state.trace_index]
            event_type = event.get('type', 'EVENT').upper()
            event_msg = event.get('message', '')
            st.markdown(
                f"<span style='color:var(--magenta)'>[{event_type}]</span> "
                f"<span style='color:var(--green)'>{event_msg}</span>"
                f"<span style='animation: blink 1s step-end infinite;'>_</span>",
                unsafe_allow_html=True,
            )
            if event.get("errors"):
                for err in event["errors"]:
                    st.markdown(f"<div style='color:var(--magenta); font-family: monospace; margin: 4px 0 4px 15px;'>&gt; {err}</div>", unsafe_allow_html=True)
            if event.get("board"):
                render_board(event.get("board"), title=None, original_board=st.session_state.board_data)

st.markdown("<hr style='border-color: var(--muted);'><div style='text-align: right; font-family: monospace; color: var(--muted); font-size: 12px;'>SYS.STATUS: ONLINE // TERMINAL: SUDOKUX_V1.0.4 <span style='animation: blink 1s step-end infinite; color: var(--cyan)'>█</span></div>", unsafe_allow_html=True)
