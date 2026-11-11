import unittest
from copy import deepcopy
from solver.difficulty import analyze_difficulty
from experiments.benchmark_puzzles import PUZZLES
from solver.puzzle_generator import generate_demo_puzzle
from solver.backtracking import SudokuSolver


class TestDifficultyAnalyzer(unittest.TestCase):
    def test_returns_explainable_metrics(self):
        result = analyze_difficulty(deepcopy(PUZZLES["Puzzle_1"]))
        self.assertTrue(result["valid"])
        self.assertIn(result["difficulty"], {"Easy", "Medium", "Hard", "Expert"})
        self.assertGreater(result["empty_cells"], 0)
        self.assertIn("method", result)
        self.assertGreaterEqual(result["complexity_score"], 0)

    def test_generated_demo_puzzle_has_valid_completion(self):
        puzzle = generate_demo_puzzle(seed=7, empty_cells=48)
        self.assertEqual(sum(v == 0 for row in puzzle for v in row), 48)
        solver = SudokuSolver(puzzle, use_mrv=True, use_ac3=True)
        self.assertFalse(solver.validation_errors)
        self.assertTrue(solver.solve())

    def test_invalid_board_reported(self):
        result = analyze_difficulty([[1] * 9 for _ in range(9)])
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
