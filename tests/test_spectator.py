# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Exercise spectator controls with real Tk events and a controllable engine."""

from pathlib import Path
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from gomoku.app import GomokuApp
from gomoku.game import Stone


class TestEngine:
    available = True
    sequence = [(7, 7), (0, 0), (8, 7), (0, 1), (9, 7), (0, 2), (10, 7), (0, 3), (11, 7)]

    def __init__(self):
        self.release = threading.Event()
        self.release.set()
        self.entered = threading.Event()
        self.failure = None

    def best_move(self, snapshot, **options):
        self.entered.set()
        if not self.release.wait(2):
            raise RuntimeError("test search was not released")
        if self.failure:
            raise self.failure
        return self.sequence[len(snapshot)]

    def stop(self):
        self.release.set()

    def close(self):
        self.release.set()


class SpectatorTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.root.withdraw()
        self.app = GomokuApp(self.root, Path(__file__).resolve().parents[1])
        self.engine = TestEngine()
        self.app.engine = self.engine
        self.app.ai_delay = 1

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.on_close()

    def pump_until(self, condition, timeout=3):
        deadline = time.monotonic() + timeout
        while not condition() and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.005)
        self.assertTrue(condition(), "Tk operation did not complete")

    def test_autoplay_alternates_until_win_and_stops(self):
        self.app._set_mode("ai")
        self.pump_until(lambda: self.app.board.result.finished)
        self.assertEqual(self.app.board.result.winner, Stone.BLACK)
        self.assertEqual(len(self.app.board.moves), 9)
        self.assertEqual([m.stone for m in self.app.board.moves], [Stone.BLACK, Stone.WHITE] * 4 + [Stone.BLACK])
        self.assertIsNone(self.app.ai_timer)
        self.assertEqual(self.app.pause_button["state"], "disabled")

    def test_pause_step_and_undo_keep_position_paused(self):
        self.app._set_mode("ai")
        self.app.toggle_ai_pause()
        self.root.update()
        self.assertEqual(len(self.app.board.moves), 0)
        self.app.step_ai()
        self.pump_until(lambda: len(self.app.board.moves) == 1)
        self.assertTrue(self.app.ai_paused)
        self.assertIsNone(self.app.ai_timer)
        self.app.step_ai()
        self.pump_until(lambda: len(self.app.board.moves) == 2)
        self.app.undo()
        self.assertEqual(len(self.app.board.moves), 1)
        self.assertTrue(self.app.ai_paused)
        self.app.toggle_ai_pause()
        self.pump_until(lambda: self.app.board.result.finished)

    def test_pause_during_search_discards_result(self):
        self.engine.release.clear()
        self.app._set_mode("ai")
        self.pump_until(self.engine.entered.is_set)
        self.app.toggle_ai_pause()
        self.pump_until(lambda: not self.app.search_active)
        self.assertEqual(len(self.app.board.moves), 0)
        self.app.step_ai()
        self.pump_until(lambda: len(self.app.board.moves) == 1)

    def test_restart_and_mode_change_discard_inflight_result(self):
        self.engine.release.clear()
        self.app._set_mode("ai")
        self.pump_until(self.engine.entered.is_set)
        self.app.new_game()
        self.app._set_mode("double")
        self.pump_until(lambda: not self.app.search_active)
        self.assertEqual(len(self.app.board.moves), 0)
        self.assertIsNone(self.app.ai_timer)
        self.app.board.place(5, 5)
        self.app._update_status()
        self.assertEqual(self.app.board.current_player, Stone.WHITE)

    def test_single_white_still_requests_black_ai(self):
        self.app._set_human_color(Stone.WHITE)
        self.pump_until(lambda: len(self.app.board.moves) == 1)
        self.assertEqual(self.app.board.current_player, Stone.WHITE)
        self.assertIsNone(self.app.ai_timer)

    def test_engine_failure_pauses_and_reports_error(self):
        self.engine.failure = RuntimeError("engine test failure")
        with patch("gomoku.app.messagebox.showerror") as show_error:
            self.app._set_mode("ai")
            self.pump_until(lambda: self.app.ai_paused)
            self.assertEqual(len(self.app.board.moves), 0)
            self.assertFalse(self.app.thinking)
            self.assertIsNone(self.app.ai_timer)
            self.assertIn("engine test failure", show_error.call_args.args[1])

    def test_spectator_controls_fit_minimum_window(self):
        self.app._set_mode("ai")
        self.app.toggle_ai_pause()
        self.root.geometry("900x660")
        self.root.deiconify()
        self.root.update()
        bottom = self.root.winfo_rooty() + self.root.winfo_height()
        for widget in (self.app.pause_button, self.app.step_button, self.app.undo_button, self.app.new_button):
            self.assertTrue(widget.winfo_ismapped(), widget["text"])
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), bottom)
        self.assertGreaterEqual(self.app.moves_text.winfo_height(), 50)


if __name__ == "__main__":
    unittest.main()
