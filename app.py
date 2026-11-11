"""
SudokuX — simple, manual-entry Sudoku workbench.
Run with: streamlit run app.py
"""
from copy import deepcopy
from time import perf_counter

import pandas as pd
import streamlit as st

from solver.backtracking import SudokuSolver
from solver.difficulty import analyze_difficulty
from experiments.benchmark import ALGORITHMS, run_once
from experiments.benchmark_puzzles import PUZZLES

st.set_page_config(
    page_title="SudokuX | Sudoku Workbench",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------- Styling --------------------------------------
st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 1.5rem; padding-bottom: 3rem;}
      
      /* Hero Section */
      .hero {
          padding: 1.5rem 1.8rem; 
          background: linear-gradient(135deg, rgba(128,128,128,0.05) 0%, rgba(128,128,128,0.15) 100%);
          border: 1px solid rgba(128,128,128,.2);
          border-radius: 16px; 
          margin-bottom: 1.5rem;
          box-shadow: 0 4px 12px rgba(0,0,0,0.03);
      }
      .hero h1 {margin: 0 0 .35rem 0; font-size: 2.2rem; font-weight: 800;}
      .hero p {margin: 0; color: #777; font-size: 1.05rem;}
      
      .section-note {color:#777; font-size:.95rem; margin-top:-.5rem; margin-bottom: 1rem;}
      
      /* Data Editor Customization */
      div[data-testid="stDataEditor"] {
          max-width: 460px; 
          margin: 0 auto;
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
          border-radius: 4px;
      }
      div[data-testid="stDataEditor"] [role="columnheader"] {display:none;}
      
      /* Metric Cards */
      [data-testid="stMetric"] {
          background-color: rgba(128,128,128,0.03);
          border: 1px solid rgba(128,128,128,.15);
          padding: 1rem 1.2rem; 
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.02);
      }
      
      /* HTML Custom Sudoku Board (for solutions/tracing) */
      .sudoku-container { display: flex; justify-content: center; margin: 1.5rem 0; }
      .sudoku-table {
          border-collapse: collapse;
          border: 3px solid var(--text-color);
          background-color: var(--background-color);
          font-family: monospace;
          font-size: 1.4rem;
          box-shadow: 0 6px 16px rgba(0,0,0,0.08);
      }
      .sudoku-table td {
          width: 46px; height: 46px;
          text-align: center; vertical-align: middle;
          border: 1px solid rgba(128, 128, 128, 0.3);
      }
      .sudoku-table .thick-right { border-right: 3px solid var(--text-color); }
      .sudoku-table .thick-bottom { border-bottom: 3px solid var(--text-color); }
      .sudoku-table .given { font-weight: 800; color: var(--text-color); }
      .sudoku-table .solved { font-weight: 700; color: #0078D7; }
      .sudoku-table .bg-alt { background-color: rgba(128, 128, 128, 0.08); }
      
      div.stButton > button {border-radius:9px; min-height:2.6rem; font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Session state --------------------------------
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
    """Renders a beautiful, read-only HTML Sudoku board for solutions and traces."""
    if title:
        st.markdown(f"<h4 style='text-align: center; margin-bottom: -0.5rem;'>{title}</h4>", unsafe_allow_html=True)
        
    html = '<div class="sudoku-container"><table class="sudoku-table">'
    for r in range(9):
        html += "<tr>"
        for c in range(9):
            val = board[r][c]
            val_str = str(val) if val != 0 else ""
            classes = []
            
            # Thick Borders
            if c in (2, 5): classes.append("thick-right")
            if r in (2, 5): classes.append("thick-bottom")
            
            # Alternating 3x3 background colors
            if (r // 3 + c // 3) % 2 == 0: classes.append("bg-alt")
            
            # Highlight original clues vs newly solved numbers
            if original_board and original_board[r][c] != 0:
                classes.append("given")
            elif val != 0:
                classes.append("solved")
                
            class_str = " ".join(classes)
            html += f'<td class="{class_str}">{val_str}</td>'
        html += "</tr>"
    html += "</table></div>"
    
    st.markdown(html, unsafe_allow_html=True)

def metrics_row(metrics):
    a, b, c, d = st.columns(4)
    a.metric("Search nodes", metrics.get("nodes_explored", 0))
    b.metric("Backtracks", metrics.get("backtracks", 0))
    c.metric("Constraint checks", metrics.get("constraint_checks", 0))
    d.metric("Runtime", f"{metrics.get('time_ms', 0):.3f} ms")


# ----------------------------- Header ---------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>🧩 SudokuX</h1>
      <p>Enter a Sudoku. Inspect its difficulty. Compare solving strategies. Get the solution.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Sample puzzles -------------------------------
sample_labels = {
    "Sample 1 — Starter": "Puzzle_1",
    "Sample 2 — Intermediate": "Puzzle_2",
    "Sample 3 — Challenge": "Puzzle_3",
    "Sample 4 — Expert demo": "Puzzle_4",
}
top_left, top_mid, top_right = st.columns([2.1, 1, 1])
with top_left:
    selected_sample = st.selectbox("Load a sample puzzle", list(sample_labels.keys()), label_visibility="collapsed")
with top_mid:
    if st.button("Load sample", use_container_width=True):
        load_board(PUZZLES[sample_labels[selected_sample]])
        st.rerun()
with top_right:
    if st.button("Clear board", use_container_width=True):
        load_board([[0] * 9 for _ in range(9)])
        st.rerun()

st.markdown("### Enter your Sudoku")
st.markdown(
    '<p class="section-note">Type numbers from 1 to 9. Leave unknown cells as 0. '
    'The 3 × 3 blocks are highlighted for clarity.</p>',
    unsafe_allow_html=True,
)

# Connected 9x9 Sudoku grid using Streamlit's editable table.
revision = st.session_state.board_revision
column_names = [f"C{i}" for i in range(1, 10)]
grid_df = pd.DataFrame(st.session_state.board_data, columns=column_names)

def sudoku_grid_style(df):
    """Styles the editable pandas dataframe to look like a true Sudoku board."""
    styles = pd.DataFrame("", index=range(9), columns=column_names)
    for r in range(9):
        for c in range(9):
            val = df.iat[r, c]
            css = [
                "text-align: center",
                "font-size: 22px",
                "font-weight: 700",
                "font-family: monospace",
                "border: 1px solid rgba(128, 128, 128, 0.2)",
            ]
            
            # Checkerboard background for 3x3 grids
            if (r // 3 + c // 3) % 2 == 0:
                css.append("background-color: rgba(128, 128, 128, 0.08)")
            else:
                css.append("background-color: transparent")
                
            # Make 0s completely transparent so they act as "empty" cells visually
            if val == 0:
                css.append("color: transparent")
            else:
                css.append("color: var(--text-color)")

            # Strong grid lines
            if c in (2, 5): css.append("border-right: 3px solid var(--text-color)")
            if r in (2, 5): css.append("border-bottom: 3px solid var(--text-color)")
            if c == 0: css.append("border-left: 3px solid var(--text-color)")
            if r == 0: css.append("border-top: 3px solid var(--text-color)")
            if c == 8: css.append("border-right: 3px solid var(--text-color)")
            if r == 8: css.append("border-bottom: 3px solid var(--text-color)")

            styles.iat[r, c] = ";".join(css)
    return styles

styled_grid = grid_df.style.apply(sudoku_grid_style, axis=None)

column_config = {
    col: st.column_config.NumberColumn(
        label="",
        min_value=0,
        max_value=9,
        step=1,
        format="%d",
        width="small",
    )
    for col in column_names
}

# The grid editor
edited_grid = st.data_editor(
    styled_grid,
    key=f"sudoku_grid_{revision}",
    column_config=column_config,
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    height=425,
    disabled=False,
)

# Convert the edited table back to the solver's 9x9 list format.
board_input = edited_grid[column_names].fillna(0).astype(int).values.tolist()

if board_input != st.session_state.board_data:
    st.session_state.board_data = deepcopy(board_input)
    invalidate_results()

# ----------------------------- Main actions ---------------------------------
st.divider()
st.markdown("### What would you like to do?")
opt1, opt2, opt3 = st.columns([1, 1, 1.35])
with opt1:
    difficulty_on = st.toggle("Difficulty analyzer", value=False, help="Estimate puzzle difficulty using the reference CSP solver.")
with opt2:
    analysis_on = st.toggle("Algorithm comparison", value=False, help="Run all configured algorithms on the same puzzle.")
with opt3:
    strategy_names = {
        "Recommended — AC-3 + MRV + Degree": "AC3 + MRV + Degree + FC",
        "Fast baseline — MRV": "BT + MRV",
        "Simple — Basic backtracking": "Basic BT",
        "Full — AC-3 + MRV + Degree + LCV + FC": "Full AI (AC3 + MRV + Degree + LCV + FC)",
    }
    chosen_strategy = st.selectbox("Solution method", list(strategy_names.keys()), label_visibility="collapsed")

action_col, reset_col = st.columns([2, 1])
with action_col:
    solve_clicked = st.button("✓  Generate solution", type="primary", use_container_width=True)
with reset_col:
    if st.button("Reset results", use_container_width=True):
        invalidate_results()
        st.rerun()

if solve_clicked:
    config = ALGORITHMS[strategy_names[chosen_strategy]]
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

# ----------------------------- Difficulty panel ----------------------------
if difficulty_on:
    with st.container(border=True):
        st.markdown("### Difficulty analysis")
        result = analyze_difficulty(st.session_state.board_data)
        st.session_state.difficulty_result = result
        if not result.get("valid"):
            st.error("This puzzle is invalid.")
            for err in result.get("errors", []):
                st.write(f"• {err}")
        elif not result.get("solvable"):
            st.warning("The clues are valid, but the puzzle has no solution.")
        else:
            level = result["difficulty"]
            st.markdown(f"**Estimated difficulty: {level}**")
            x1, x2, x3, x4 = st.columns(4)
            x1.metric("Empty cells", result["empty_cells"])
            x2.metric("Candidate values", result["initial_candidate_count"])
            x3.metric("Forced cells", result["initial_forced_cells"])
            x4.metric("Effort score", result["complexity_score"])
            st.caption(
                f"Reference solver: {result['reference_nodes']} nodes · "
                f"{result['reference_backtracks']} backtracks · "
                f"{result['reference_time_ms']:.3f} ms"
            )
            st.info(result["method"])
            st.caption("Difficulty is an estimate from this project's solver metrics, not an official human Sudoku rating.")

# ----------------------------- Solution panel ------------------------------
if st.session_state.solve_result:
    result = st.session_state.solve_result
    with st.container(border=True):
        st.markdown("### Solution")
        if result["errors"]:
            st.error("Input validation failed.")
            for err in result["errors"]:
                st.write(f"• {err}")
        elif result["solved"]:
            st.success(f"Solved using: {result['method']}")
            render_board(result["solution"], original_board=st.session_state.board_data)
            st.markdown("**Solver performance**")
            metrics_row(result["metrics"])
        else:
            st.error("No solution found for this puzzle using the selected method.")
            metrics_row(result["metrics"])

# ----------------------------- Comparison panel -----------------------------
if analysis_on:
    with st.container(border=True):
        st.markdown("### Algorithm comparison")
        st.write("Every method receives the exact same input puzzle. Runtime is averaged; search counters are reported from a representative run.")
        run_count = st.select_slider("Runtime repetitions", options=[1, 2, 3, 5], value=3)
        if st.button("Run comparison", use_container_width=True):
            rows = []
            progress = st.progress(0.0)
            algorithms = list(ALGORITHMS.items())
            for index, (name, config) in enumerate(algorithms):
                runs = [run_once(st.session_state.board_data, config) for _ in range(run_count)]
                first = runs[0]
                rows.append({
                    "Algorithm": name,
                    "Solved": all(x["solved"] for x in runs),
                    "Mean time (ms)": round(sum(x["time_ms"] for x in runs) / run_count, 3),
                    "Nodes": first["nodes_explored"],
                    "Backtracks": first["backtracks"],
                    "Constraint checks": first["constraint_checks"],
                    "Assignments": first["assignments"],
                    "AC-3 values removed": first["ac3_values_removed"],
                })
                progress.progress((index + 1) / len(algorithms))
            st.session_state.battle_result = pd.DataFrame(rows)
        if st.session_state.battle_result is not None:
            st.dataframe(st.session_state.battle_result, hide_index=True, use_container_width=True)
            data = st.session_state.battle_result.set_index("Algorithm")
            tab1, tab2, tab3 = st.tabs(["Search effort", "Constraint checks", "Runtime"])
            with tab1:
                st.bar_chart(data[["Nodes", "Backtracks"]])
            with tab2:
                st.bar_chart(data[["Constraint checks", "AC-3 values removed"]])
            with tab3:
                st.bar_chart(data[["Mean time (ms)"]])

# ----------------------------- Explainability -------------------------------
if st.session_state.trace_events:
    with st.expander("How did the solver reach this answer? — reasoning replay"):
        events = st.session_state.trace_events
        max_index = len(events) - 1
        st.caption(f"{len(events)} recorded events. Use the slider to inspect decisions, propagation and backtracking.")
        selected_event = st.slider(
            "Reasoning step", min_value=1, max_value=max(1, len(events)),
            value=min(st.session_state.trace_index + 1, len(events)),
            key="trace_slider",
        )
        st.session_state.trace_index = selected_event - 1
        event = events[st.session_state.trace_index]
        st.write(f"**{event['type'].upper()}** — {event['message']}")
        event_board = event.get("board")
        if event_board:
            render_board(event_board, "Board at this step", original_board=st.session_state.board_data)

# ----------------------------- Footer ----------------------------------------
st.divider()
st.caption(
    "SudokuX is an educational constraint-satisfaction project. "
    "AC-3 here operates on pairwise inequality constraints; difficulty labels are project-defined estimates."
)