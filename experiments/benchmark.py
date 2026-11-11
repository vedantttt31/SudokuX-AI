"""Repeatable multi-puzzle algorithm benchmark; writes measured CSV results."""
import csv
from copy import deepcopy
from pathlib import Path
from statistics import mean, stdev
from time import perf_counter
from solver.backtracking import SudokuSolver
from experiments.benchmark_puzzles import PUZZLES

RUNS_PER_EXPERIMENT = 3
ALGORITHMS = {
    "Basic BT": dict(),
    "BT + MRV": {"use_mrv": True},
    "BT + FC": {"use_forward_checking": True},
    "MRV + FC": {"use_mrv": True, "use_forward_checking": True},
    "AC3 + MRV": {"use_mrv": True, "use_ac3": True},
    "MRV + Degree + LCV + FC": {
        "use_mrv": True, "use_degree": True, "use_lcv": True,
        "use_forward_checking": True
    },
    "AC3 + MRV + Degree + FC": {
        "use_mrv": True, "use_degree": True, "use_ac3": True,
        "use_forward_checking": True
    },
    "Full AI (AC3 + MRV + Degree + LCV + FC)": {
        "use_mrv": True, "use_degree": True, "use_lcv": True,
        "use_ac3": True, "use_forward_checking": True
    },
}


def run_once(board, config):
    solver = SudokuSolver(deepcopy(board), **config)
    start = perf_counter()
    solved = solver.solve()
    elapsed = (perf_counter() - start) * 1000
    return {"solved": solved, "time_ms": elapsed, **solver.get_metrics()}


def run_benchmark(puzzles=None, runs=RUNS_PER_EXPERIMENT):
    puzzles = puzzles or PUZZLES
    rows = []
    for puzzle_name, board in puzzles.items():
        for algorithm, config in ALGORITHMS.items():
            measurements = [run_once(board, config) for _ in range(runs)]
            first = measurements[0]
            rows.append({
                "puzzle": puzzle_name,
                "algorithm": algorithm,
                "solved": all(x["solved"] for x in measurements),
                "runs": runs,
                "time_ms_mean": round(mean(x["time_ms"] for x in measurements), 4),
                "time_ms_stdev": round(stdev(x["time_ms"] for x in measurements), 4) if runs > 1 else 0,
                **{k: first[k] for k in first if k not in ("solved", "time_ms")}
            })
    return rows


def save_csv(rows, path=None):
    path = Path(path or "experiments/results/benchmark_results.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No benchmark rows to save.")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    data = run_benchmark()
    output = save_csv(data)
    print(f"Completed {len(data)} benchmark cases. Results: {output}")
    for row in data:
        print(f"{row['puzzle']:<12} {row['algorithm']:<28} nodes={row['nodes_explored']:<7} "
              f"backtracks={row['backtracks']:<7} time={row['time_ms_mean']:.3f} ms")
