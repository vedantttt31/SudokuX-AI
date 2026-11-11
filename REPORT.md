# SudokuX — Project Technical Report

## 1. Objective

Investigate how CSP modelling, inference and heuristic search reduce the search effort needed to solve Sudoku compared with plain backtracking.

## 2. CSP formulation

- **Variables:** one variable `X(r,c)` for each of the 81 cells.
- **Domains:** `{1,2,3,4,5,6,7,8,9}` for empty cells; a singleton containing the clue for fixed cells.
- **Constraints:** for every pair of peer cells sharing a row, column or 3×3 box, `X_i != X_j`.

The input validator checks that the supplied clues do not already violate these constraints.

## 3. Algorithms

### Basic backtracking

Select the first unassigned cell, try legal values, recurse, and undo an assignment when a branch fails. This is the baseline search procedure.

### Minimum Remaining Values (MRV)

Select the unassigned variable with the smallest current domain. This attempts the most constrained variable first and exposes failure early.

### Degree heuristic

When MRV produces a tie, select the variable that has the greatest number of unassigned peers. It is a tie-breaker, not a replacement for MRV.

### Forward checking

After a tentative assignment, inspect its unassigned peers. If any peer has no legal value left, reject the branch immediately.

### AC-3

Treat each peer relationship as a binary inequality constraint. Revise domains by removing a value that has no supporting unequal value in a neighbouring domain. Repeat until the queue is empty or a domain becomes empty.

### Least Constraining Value (LCV)

LCV orders a selected variable's candidate values by how many values they would remove from unassigned peer domains. It tries the candidate with the smallest immediate impact first. This is a value-ordering heuristic: it does not change which values are legal, but can influence how quickly search finds a solution.

### Combined solver

The strongest configuration combines AC-3, MRV, Degree tie-breaking, LCV value ordering, forward checking and recursive backtracking. Each mechanism has a distinct role: inference reduces domains, MRV chooses a constrained variable, Degree breaks ties, FC checks immediate neighbours, and backtracking guarantees systematic search.

## 4. Explainability

The solver can record events for CSP initialization, variable selection, candidate lists, tentative values, accepted assignments, domain wipeouts, backtracking and completion. Every event includes a board snapshot so the Streamlit interface can replay the decision sequence.

## 5. Experimental design

`experiments/benchmark.py` runs eight algorithm configurations against the same fixed puzzle set. Each configuration is repeated; runtime is averaged, while deterministic search counters are taken from the first run. The script exports raw measurements to CSV. `experiments/plot_results.py` produces charts for nodes, backtracks, constraint checks and runtime.

Do not claim that one method is universally fastest based on one puzzle. Compare across the included fixtures and report the machine/runtime environment. Search counters and wall-clock runtime answer different questions: a method may reduce search but add propagation overhead.

### Sample measured outcomes (this development run)

The benchmark executed 32 cases: four fixed puzzles × eight configurations, with three timing repetitions per case. All 32 cases solved successfully. Minimum-node configurations observed in this run were:

| Puzzle fixture | Lowest-node strategy | Nodes | Backtracks | Mean time (ms) |
|---|---|---:|---:|---:|
| Puzzle 1 | BT + MRV | 51 | 0 | 4.451 |
| Puzzle 2 | BT + MRV | 45 | 0 | 0.661 |
| Puzzle 3 | MRV + Degree + LCV + FC | 57 | 0 | 29.852 |
| Puzzle 4 | AC-3 + MRV | 72 | 22 | 180.002 |

These timings are machine- and load-dependent. They illustrate why fewer search nodes do not guarantee lower wall-clock time: AC-3 incurs propagation overhead. LCV was very helpful on Puzzle 3 (57 nodes, no backtracks) but the full LCV combination explored more nodes than AC-3 + MRV on Puzzle 4. Value ordering is puzzle-dependent, not a universal speed-up. The complete measurements are in `experiments/results/benchmark_results.csv`.

## 6. Difficulty estimate

The analyzer measures empty cells, initial candidate count, average and maximum domain size, forced initial cells, and search effort under one fixed reference configuration. It calculates a composite effort score: `nodes + 2 × backtracks + 10 × max(0, average_domain_size − 3) + 0.25 × empty_cells − 2 × forced_initial_cells`. Project-defined bands are up to 75 (Easy), 76–300 (Medium), 301–1,500 (Hard), and above 1,500 (Expert). These thresholds are transparent and reproducible, but they are not an externally standardized Sudoku difficulty rating.

## 7. Limitations

- AC-3 uses binary pairwise inequality constraints and is weaker than specialized global `AllDifferent` propagation.
- The demo generator removes cells from a valid completed pattern but does not check uniqueness.
- Difficulty is an algorithmic estimate under a fixed solver, not a measure of human solving difficulty.
- Runtime depends on CPU, Python version and system load.
- The reasoning trace is a recorded replay of a completed run, not an interactive search paused mid-recursion.

## 8. Future work

A uniqueness-checking puzzle generator, stronger global constraint propagation, least-constraining-value ordering, and true pause/resume search could extend the project after the current implementation is evaluated.
