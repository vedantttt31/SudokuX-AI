"""Forward-checking utilities."""


def forward_check(solver, row, col):
    """Check that every unassigned peer retains at least one legal value."""
    peers = set()
    peers.update((row, c) for c in range(9) if c != col)
    peers.update((r, col) for r in range(9) if r != row)
    br, bc = (row // 3) * 3, (col // 3) * 3
    peers.update((r, c) for r in range(br, br+3) for c in range(bc, bc+3))
    for r, c in peers:
        if solver.board[r][c] != 0:
            continue
        if not any(solver.is_valid(r, c, n) for n in range(1, 10)):
            solver.forward_check_failures += 1
            return False
    return True
