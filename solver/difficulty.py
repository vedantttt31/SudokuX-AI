"""Explainable, heuristic difficulty estimate using a fixed reference solver."""
from copy import deepcopy
from solver.backtracking import SudokuSolver
from solver.heuristics import get_candidates


def analyze_difficulty(board):
    """Estimate puzzle difficulty; this is a project heuristic, not a rating standard."""
    probe = SudokuSolver(deepcopy(board))
    if probe.validation_errors:
        return {"valid": False, "errors": probe.validation_errors}

    empty_cells = sum(v == 0 for row in board for v in row)
    domain_sizes = [len(get_candidates(probe, r, c)) for r in range(9) for c in range(9) if board[r][c] == 0]
    initial_candidates = sum(domain_sizes)
    forced_cells = sum(size == 1 for size in domain_sizes)

    reference = SudokuSolver(
        deepcopy(board), use_mrv=True, use_degree=True, use_lcv=True,
        use_forward_checking=True, use_ac3=True
    )
    solved = reference.solve()
    metrics = reference.get_metrics()
    nodes = metrics["nodes_explored"]

    # Composite effort score prevents a puzzle with many broad domains but an
    # easy first-found completion from being rated solely by its node count.
    average_domain = (initial_candidates / empty_cells) if empty_cells else 0
    complexity_score = round(
        nodes + 2 * metrics["backtracks"]
        + 10 * max(0, average_domain - 3)
        + 0.25 * empty_cells
        - 2 * forced_cells,
        2,
    )
    if not solved:
        level = "Unsolvable"
        rationale = "The reference solver could not find a completion."
    elif complexity_score <= 75:
        level = "Easy"
        rationale = f"Composite effort score {complexity_score} is at most 75."
    elif complexity_score <= 300:
        level = "Medium"
        rationale = f"Composite effort score {complexity_score} is between 76 and 300."
    elif complexity_score <= 1_500:
        level = "Hard"
        rationale = f"Composite effort score {complexity_score} is between 301 and 1,500."
    else:
        level = "Expert"
        rationale = f"Composite effort score {complexity_score} exceeds 1,500."

    return {
        "valid": True,
        "solvable": solved,
        "difficulty": level,
        "empty_cells": empty_cells,
        "initial_candidate_count": initial_candidates,
        "average_domain_size": round(initial_candidates / empty_cells, 2) if empty_cells else 0,
        "maximum_domain_size": max(domain_sizes, default=0),
        "initial_forced_cells": forced_cells,
        "complexity_score": complexity_score,
        "reference_nodes": nodes,
        "reference_backtracks": metrics["backtracks"],
        "reference_time_ms": round(metrics["time_ms"], 3),
        "rationale": rationale,
        "method": "Fixed reference strategy: AC-3 + MRV + Degree + LCV + Forward Checking. Thresholds are project-defined and should not be confused with human Sudoku ratings."
    }
