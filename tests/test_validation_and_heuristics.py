import unittest

from solver.backtracking import SudokuSolver
from solver.heuristics import count_unassigned_neighbors, find_mrv_cell


VALID_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


class TestInputValidation(unittest.TestCase):
    def test_valid_board_accepted(self):
        solver = SudokuSolver([row[:] for row in VALID_PUZZLE])
        self.assertEqual(solver.validation_errors, [])
        self.assertTrue(solver.solve())

    def test_duplicate_in_row_rejected(self):
        board = [row[:] for row in VALID_PUZZLE]
        board[0][2] = 5
        solver = SudokuSolver(board)
        self.assertFalse(solver.solve())
        self.assertTrue(any("row 1" in e.lower() for e in solver.validation_errors))

    def test_duplicate_in_column_rejected(self):
        board = [row[:] for row in VALID_PUZZLE]
        board[2][0] = 5
        solver = SudokuSolver(board)
        self.assertFalse(solver.solve())
        self.assertTrue(any("column 1" in e.lower() for e in solver.validation_errors))

    def test_duplicate_in_box_rejected(self):
        board = [row[:] for row in VALID_PUZZLE]
        board[1][1] = 5
        solver = SudokuSolver(board)
        self.assertFalse(solver.solve())
        self.assertTrue(any("box" in e.lower() for e in solver.validation_errors))

    def test_invalid_shape_rejected(self):
        solver = SudokuSolver([[0] * 9 for _ in range(8)])
        self.assertFalse(solver.solve())
        self.assertTrue(solver.validation_errors)

    def test_invalid_value_rejected(self):
        board = [row[:] for row in VALID_PUZZLE]
        board[0][2] = 10
        solver = SudokuSolver(board)
        self.assertFalse(solver.solve())
        self.assertTrue(solver.validation_errors)


class TestDegreeHeuristic(unittest.TestCase):
    def test_degree_count_is_nonnegative(self):
        solver = SudokuSolver([row[:] for row in VALID_PUZZLE])
        degree = count_unassigned_neighbors(solver, 0, 2)
        self.assertGreaterEqual(degree, 0)

    def test_mrv_with_degree_returns_empty_cell_and_domain(self):
        solver = SudokuSolver([row[:] for row in VALID_PUZZLE],
                              use_mrv=True, use_degree=True)
        cell, candidates = find_mrv_cell(solver, use_degree=True)
        self.assertIsNotNone(cell)
        self.assertEqual(solver.board[cell[0]][cell[1]], 0)
        self.assertGreater(len(candidates), 0)

    def test_solver_with_degree_solves(self):
        solver = SudokuSolver([row[:] for row in VALID_PUZZLE],
                              use_mrv=True, use_degree=True)
        self.assertTrue(solver.solve())


if __name__ == "__main__":
    unittest.main()
