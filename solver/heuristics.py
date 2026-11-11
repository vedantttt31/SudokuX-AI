"""Variable ordering heuristics for Sudoku CSP."""


def get_candidates(solver, row, col):
    return [n for n in range(1, 10) if solver.is_valid(row, col, n)]


def count_unassigned_neighbors(solver, row, col):
    peers = set()
    peers.update((row, c) for c in range(9) if c != col)
    peers.update((r, col) for r in range(9) if r != row)
    br, bc = (row // 3) * 3, (col // 3) * 3
    peers.update((r, c) for r in range(br, br+3) for c in range(bc, bc+3))
    return sum(1 for r, c in peers if solver.board[r][c] == 0)


def find_mrv_cell(solver, domains=None, use_degree=False):
    best_cell, best_values, best_degree = None, None, -1
    for r in range(9):
        for c in range(9):
            if solver.board[r][c] != 0:
                continue
            values = list(domains[(r, c)]) if domains is not None else get_candidates(solver, r, c)
            degree = count_unassigned_neighbors(solver, r, c) if use_degree else 0
            if (best_cell is None or len(values) < len(best_values) or
                (use_degree and len(values) == len(best_values) and degree > best_degree)):
                best_cell, best_values, best_degree = (r, c), values, degree
            if not use_degree and len(best_values) == 1:
                return best_cell, best_values
    return best_cell, best_values



def order_values_lcv(solver, cell, candidates, domains=None):
    """
    Least Constraining Value (LCV): try the value that removes the fewest
    options from the cell's currently unassigned peers.
    """
    row, col = cell
    peers = set()
    peers.update((row, c) for c in range(9) if c != col)
    peers.update((r, col) for r in range(9) if r != row)
    br, bc = (row // 3) * 3, (col // 3) * 3
    peers.update((r, c) for r in range(br, br + 3) for c in range(bc, bc + 3))
    peers = [(r, c) for r, c in peers if solver.board[r][c] == 0]

    def elimination_count(value):
        conflicts = 0
        for peer in peers:
            if domains is not None:
                if value in domains[peer]:
                    conflicts += 1
            elif solver.is_valid(peer[0], peer[1], value):
                conflicts += 1
        return conflicts

    return sorted(candidates, key=lambda value: (elimination_count(value), value))
