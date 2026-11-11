"""Generate experiment charts from the measured benchmark CSV."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = Path("experiments/results/benchmark_results.csv")
OUT = Path("experiments/results/plots")


def generate_plots(csv_path=DATA, output_dir=OUT):
    df = pd.read_csv(csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = [
        ("nodes_explored", "Search nodes by algorithm", "Nodes explored", "nodes.png"),
        ("backtracks", "Backtracks by algorithm", "Backtracks", "backtracks.png"),
        ("constraint_checks", "Constraint checks by algorithm", "Constraint checks", "constraint_checks.png"),
        ("time_ms_mean", "Mean execution time by algorithm", "Time (ms)", "runtime.png"),
    ]
    for metric, title, ylabel, filename in metrics:
        pivot = df.pivot(index="puzzle", columns="algorithm", values=metric)
        ax = pivot.plot(kind="bar", figsize=(14, 7))
        ax.set_title(title)
        ax.set_xlabel("Puzzle")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=0)
        ax.legend(title="Algorithm", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig(output_dir / filename, dpi=180)
        plt.close()
    return [output_dir / item[3] for item in metrics]


if __name__ == "__main__":
    for path in generate_plots():
        print(path)
