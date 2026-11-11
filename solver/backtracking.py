"""Constraint-driven Sudoku CSP solver with optional inference heuristics."""
from __future__ import annotations

from copy import deepcopy
from time import perf_counter

from solver.heuristics import get_candidates, find_mrv_cell, order_values_lcv
from solver.ac3 import initialize_domains, ac3
from solver.propagation import forward_check


class SudokuSolver:
    def __init__(self, board, use_mrv=False, use_forward_checking=False,
                 use_ac3=False, use_degree=False, use_lcv=False, record_steps=False,
                 max_events=20000):
        self.board = deepcopy(board)
        self.use_mrv = use_mrv
        self.use_forward_checking = use_forward_checking
        self.use_ac3 = use_ac3
        self.use_degree = use_degree
        self.use_lcv = use_lcv
        self.record_steps = record_steps
        self.max_events = max_events
        self.events = []
        self.validation_errors = self.validate_board()
        self.nodes_explored = 0
        self.backtracks = 0
        self.constraint_checks = 0
        self.assignments = 0
        self.max_depth = 0
        self.forward_check_failures = 0
        self.ac3_values_removed = 0
        self.ac3_contradictions = 0
        self.ac3_arcs_processed = 0
        self.elapsed_ms = 0.0
        self.solved = False
        self.initial_board = deepcopy(self.board)

    def _event(self, kind, message, **details):
        if self.record_steps and (len(self.events) < self.max_events or kind in ("solved", "unsolved", "invalid")):
            self.events.append({"type": kind, "message": message, "board": tuple(tuple(row) for row in self.board), **details})

    def validate_board(self):
        errors = []
        if not isinstance(self.board, (list, tuple)) or len(self.board) != 9:
            return ["Board must contain exactly 9 rows."]
        for r, row in enumerate(self.board):
            if not isinstance(row, (list, tuple)) or len(row) != 9:
                return [f"Row {r + 1} must contain exactly 9 cells."]
            for c, value in enumerate(row):
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                    errors.append(f"Cell R{r+1}C{c+1} must be an integer from 0 to 9.")
        if errors:
            return errors
        for r in range(9):
            vals = [v for v in self.board[r] if v]
            if len(vals) != len(set(vals)):
                errors.append(f"Duplicate clue in row {r+1}.")
        for c in range(9):
            vals = [self.board[r][c] for r in range(9) if self.board[r][c]]
            if len(vals) != len(set(vals)):
                errors.append(f"Duplicate clue in column {c+1}.")
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                vals = [self.board[r][c] for r in range(br, br+3)
                        for c in range(bc, bc+3) if self.board[r][c]]
                if len(vals) != len(set(vals)):
                    errors.append(f"Duplicate clue in 3x3 box (rows {br+1}-{br+3}, columns {bc+1}-{bc+3}).")
        return errors

    def is_valid(self, row, col, num):
        self.constraint_checks += 1
        if any(self.board[row][c] == num for c in range(9)):
            return False
        if any(self.board[r][col] == num for r in range(9)):
            return False
        br, bc = (row // 3) * 3, (col // 3) * 3
        return not any(self.board[r][c] == num for r in range(br, br+3) for c in range(bc, bc+3))

    def find_empty_cell(self):
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    return r, c
        return None

    def _select_variable(self, domains):
        if self.use_mrv:
            return find_mrv_cell(self, domains, use_degree=self.use_degree)
        cell = self.find_empty_cell()
        if cell is None:
            return None, None
        r, c = cell
        candidates = list(domains[cell]) if domains is not None else get_candidates(self, r, c)
        return cell, candidates

    def solve(self):
        if self.validation_errors:
            self._event("invalid", "Input rejected: the starting board violates Sudoku rules.", errors=self.validation_errors)
            return False
        start = perf_counter()
        domains = initialize_domains(self) if self.use_ac3 else None
        if domains is not None:
            removed_before = self.ac3_values_removed
            if not ac3(self, domains):
                self.elapsed_ms = (perf_counter() - start) * 1000
                return False
            self._event("propagate", f"Initial AC-3 propagation removed {self.ac3_values_removed - removed_before} unsupported candidate values.")
        self._event("start", "CSP initialized. Search begins.")
        self.solved = self._search(0, domains)
        self.elapsed_ms = (perf_counter() - start) * 1000
        if self.solved:
            self._event("solved", "All 81 variables are assigned consistently.")
        else:
            self._event("unsolved", "No solution was found for this puzzle.")
        return self.solved

    def _search(self, depth, domains):
        self.max_depth = max(self.max_depth, depth)
        cell, candidates = self._select_variable(domains)
        if cell is None:
            return True
        r, c = cell
        if not candidates:
            self._event("contradiction", f"R{r+1}C{c+1} has an empty domain.", cell=cell, depth=depth)
            return False
        self.nodes_explored += 1
        strategy = "MRV" if self.use_mrv else "row-major first empty cell"
        if self.use_degree and self.use_mrv:
            strategy += " + Degree tie-break"
        self._event("select", f"Selected R{r+1}C{c+1} using {strategy}; candidates: {sorted(candidates)}.", cell=cell, candidates=sorted(candidates), depth=depth)
        if self.use_lcv:
            candidates = order_values_lcv(self, cell, candidates, domains)
            self._event("value_order", f"LCV order for R{r+1}C{c+1}: {candidates} (least peer-domain impact first).", cell=cell, candidates=list(candidates), depth=depth)
        else:
            candidates = sorted(candidates)

        for value in candidates:
            self._event("try", f"Try {value} at R{r+1}C{c+1}.", cell=cell, value=value, depth=depth)
            self.board[r][c] = value
            self.assignments += 1
            next_domains = None
            if domains is not None:
                next_domains = {k: set(v) for k, v in domains.items()}
                next_domains[cell] = {value}
                # AC-3 propagation after the tentative assignment.
                removed_before = self.ac3_values_removed
                if not ac3(self, next_domains):
                    self.board[r][c] = 0
                    self.backtracks += 1
                    self._event("contradiction", f"AC-3 found a domain wipeout after R{r+1}C{c+1}={value}.", cell=cell, value=value, depth=depth)
                    continue
                removed_now = self.ac3_values_removed - removed_before
                self._event("propagate", f"AC-3 removed {removed_now} unsupported candidate values after R{r+1}C{c+1}={value}.", cell=cell, value=value, depth=depth)
                # Keep the domains consistent with the current board assignment.
                for (rr, cc), domain in next_domains.items():
                    if self.board[rr][cc] == 0 and not domain:
                        break
            if self.use_forward_checking:
                if not forward_check(self, r, c):
                    self.board[r][c] = 0
                    self.backtracks += 1
                    self._event("contradiction", f"Forward checking found an empty neighbour domain after R{r+1}C{c+1}={value}.", cell=cell, value=value, depth=depth)
                    continue
                self._event("propagate", f"Forward checking: all unassigned peers of R{r+1}C{c+1} retain at least one candidate.", cell=cell, value=value, depth=depth)
            self._event("accept", f"Assignment R{r+1}C{c+1}={value} passed the enabled checks.", cell=cell, value=value, depth=depth)
            if self._search(depth + 1, next_domains):
                return True
            self.board[r][c] = 0
            self.backtracks += 1
            self._event("backtrack", f"Undo R{r+1}C{c+1}={value}; this branch did not lead to a solution.", cell=cell, value=value, depth=depth)
        return False

    def get_metrics(self):
        return {
            "nodes_explored": self.nodes_explored,
            "backtracks": self.backtracks,
            "constraint_checks": self.constraint_checks,
            "assignments": self.assignments,
            "max_depth": self.max_depth,
            "forward_check_failures": self.forward_check_failures,
            "ac3_values_removed": self.ac3_values_removed,
            "ac3_contradictions": self.ac3_contradictions,
            "ac3_arcs_processed": self.ac3_arcs_processed,
            "time_ms": self.elapsed_ms,
        }

    def print_metrics(self):
        for key, value in self.get_metrics().items():
            print(f"{key.replace('_', ' ').title():24}: {value}")
