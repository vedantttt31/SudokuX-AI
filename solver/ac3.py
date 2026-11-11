"""AC-3 arc consistency for the binary Sudoku CSP (Xi != Xj)."""
from collections import deque


def get_neighbors(row, col):
    peers = set((row, c) for c in range(9) if c != col)
    peers.update((r, col) for r in range(9) if r != row)
    br, bc = (row // 3) * 3, (col // 3) * 3
    peers.update((r, c) for r in range(br, br+3) for c in range(bc, bc+3))
    peers.discard((row, col))
    return peers


def initialize_domains(solver):
    domains = {}
    for r in range(9):
        for c in range(9):
            value = solver.board[r][c]
            domains[(r, c)] = {value} if value else {
                n for n in range(1, 10) if solver.is_valid(r, c, n)
            }
    return domains


def revise(domains, xi, xj, solver):
    unsupported = {x for x in domains[xi] if not any(x != y for y in domains[xj])}
    if unsupported:
        domains[xi].difference_update(unsupported)
        solver.ac3_values_removed += len(unsupported)
        return True
    return False


def ac3(solver, domains):
    queue = deque((xi, xj) for r in range(9) for c in range(9)
                  for xi in [(r, c)] for xj in get_neighbors(r, c))
    while queue:
        xi, xj = queue.popleft()
        solver.ac3_arcs_processed += 1
        if revise(domains, xi, xj, solver):
            if not domains[xi]:
                solver.ac3_contradictions += 1
                return False
            for xk in get_neighbors(*xi):
                if xk != xj:
                    queue.append((xk, xi))
    return True
