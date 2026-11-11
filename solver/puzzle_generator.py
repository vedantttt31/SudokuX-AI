"""Lightweight demo puzzle generator based on a valid Sudoku pattern."""
from copy import deepcopy
import random


def generate_demo_puzzle(seed=None, empty_cells=48):
    """Generate a puzzle with a known valid completion; uniqueness is not checked."""
    if not 0 <= empty_cells <= 81:
        raise ValueError("empty_cells must be between 0 and 81")
    rng = random.Random(seed)
    base = 3
    pattern = lambda r, c: (base * (r % base) + r // base + c) % 9
    row_order = [band * base + row for band in rng.sample(range(base), base)
                 for row in rng.sample(range(base), base)]
    col_order = [stack * base + col for stack in rng.sample(range(base), base)
                 for col in rng.sample(range(base), base)]
    digits = rng.sample(range(1, 10), 9)
    completed = [[digits[pattern(r, c)] for c in col_order] for r in row_order]
    puzzle = deepcopy(completed)
    for index in rng.sample(range(81), empty_cells):
        puzzle[index // 9][index % 9] = 0
    return puzzle
