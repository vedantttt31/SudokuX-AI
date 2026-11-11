import unittest
from copy import deepcopy
from solver.backtracking import SudokuSolver
from experiments.benchmark_puzzles import PUZZLES


class TestSudokuSolver(unittest.TestCase):
    def test_all_strategies_solve_sample_puzzles(self):
        strategies = [
            {},
            {"use_mrv": True},
            {"use_forward_checking": True},
            {"use_mrv": True, "use_forward_checking": True},
            {"use_mrv": True, "use_ac3": True},
            {"use_mrv": True, "use_degree": True, "use_forward_checking": True, "use_ac3": True},
            {"use_mrv": True, "use_degree": True, "use_lcv": True, "use_forward_checking": True, "use_ac3": True},
        ]
        for name in ("Puzzle_1", "Puzzle_2", "Puzzle_3", "Puzzle_4"):
            for config in strategies:
                with self.subTest(puzzle=name, config=config):
                    solver = SudokuSolver(deepcopy(PUZZLES[name]), **config)
                    self.assertTrue(solver.solve())
                    self.assertTrue(self.is_complete_valid(solver.board))

    def test_lcv_records_value_order_and_solves(self):
        solver = SudokuSolver(deepcopy(PUZZLES["Puzzle_1"]), use_mrv=True, use_lcv=True, record_steps=True)
        self.assertTrue(solver.solve())
        self.assertIn("value_order", {event["type"] for event in solver.events})

    def test_invalid_filled_board_is_rejected(self):
        board = [[1] * 9 for _ in range(9)]
        solver = SudokuSolver(board)
        self.assertFalse(solver.solve())
        self.assertTrue(solver.validation_errors)

    def test_trace_contains_decisions_and_solution(self):
        solver = SudokuSolver(deepcopy(PUZZLES["Puzzle_1"]), use_mrv=True, record_steps=True)
        self.assertTrue(solver.solve())
        kinds = {event["type"] for event in solver.events}
        self.assertIn("select", kinds)
        self.assertIn("try", kinds)
        self.assertIn("solved", kinds)
        self.assertTrue(all("board" in event for event in solver.events))

    @staticmethod
    def is_complete_valid(board):
        target = set(range(1, 10))
        if any(set(row) != target for row in board):
            return False
        if any({board[r][c] for r in range(9)} != target for c in range(9)):
            return False
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                if {board[r][c] for r in range(br, br+3) for c in range(bc, bc+3)} != target:
                    return False
        return True


if __name__ == "__main__":
    unittest.main()
