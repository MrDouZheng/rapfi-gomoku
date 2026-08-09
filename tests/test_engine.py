import unittest

from gomoku.engine import parse_move


class EngineProtocolTests(unittest.TestCase):
    def test_parse_move(self):
        self.assertEqual(parse_move("7,8"), (7, 8))
        self.assertEqual(parse_move(" 7, 8 "), (7, 8))

    def test_parse_move_ignores_info_and_out_of_bounds(self):
        self.assertIsNone(parse_move("INFO DEPTH 10"))
        self.assertIsNone(parse_move("15,0"))
        self.assertIsNone(parse_move("-1,0"))


if __name__ == "__main__":
    unittest.main()
