import unittest

from gomoku.game import Board, InvalidMove, Stone


class BoardTests(unittest.TestCase):
    def test_players_alternate_and_occupied_move_is_rejected(self):
        board = Board()
        self.assertEqual(board.place(7, 7).stone, Stone.BLACK)
        self.assertEqual(board.place(8, 7).stone, Stone.WHITE)
        with self.assertRaises(InvalidMove):
            board.place(7, 7)

    def test_horizontal_five_wins(self):
        board = Board()
        for x in range(5):
            board.place(x, 7)
            if x < 4:
                board.place(x, 8)
        self.assertEqual(board.result.winner, Stone.BLACK)
        self.assertEqual(board.result.winning_line, tuple((x, 7) for x in range(5)))

    def test_overline_wins_in_freestyle(self):
        board = Board()
        placements = [(0, 0), (0, 2), (1, 0), (2, 2), (3, 0), (4, 2), (4, 0), (6, 2), (5, 0), (8, 2), (2, 0)]
        for point in placements:
            board.place(*point)
        self.assertEqual(board.result.winner, Stone.BLACK)
        self.assertEqual(len(board.result.winning_line), 6)

    def test_undo_restores_turn_and_cell(self):
        board = Board()
        board.place(7, 7)
        board.place(8, 8)
        removed = board.undo(2)
        self.assertEqual(len(removed), 2)
        self.assertEqual(board.current_player, Stone.BLACK)
        self.assertEqual(board.at(7, 7), Stone.EMPTY)
        self.assertFalse(board.result.finished)


if __name__ == "__main__":
    unittest.main()
