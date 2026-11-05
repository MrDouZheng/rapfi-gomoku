# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

import sys
import time
import tkinter as tk
from pathlib import Path

from gomoku.app import GomokuApp, run
from gomoku.engine import RapfiEngine


def engine_smoke_test(project_root: Path) -> int:
    """Exercise the engine after freezing, including bundled asset extraction."""
    engine = RapfiEngine(project_root / "engine" / "pbrain-rapfi-windows-sse.exe")
    try:
        move = engine.best_move([], time_ms=300, max_depth=8)
        return 0 if move == (7, 7) else 2
    finally:
        engine.close()


def spectator_smoke_test(project_root: Path) -> int:
    """Check bundled Tk resources and both AI turns in the frozen application."""
    root = tk.Tk()
    root.withdraw()
    app = GomokuApp(root, project_root)
    try:
        app._set_mode("ai")
        app.toggle_ai_pause()
        for count in (1, 2):
            app.step_ai()
            deadline = time.monotonic() + 15
            while len(app.board.moves) < count and time.monotonic() < deadline:
                root.update()
                time.sleep(.01)
            if len(app.board.moves) != count or not app.ai_paused or app.ai_timer is not None:
                return 2
        app.undo()
        return 0 if len(app.board.moves) == 1 and app.ai_paused else 3
    finally:
        app.on_close()


if __name__ == "__main__":
    # PyInstaller extracts bundled engine assets to _MEIPASS at runtime.
    project_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    if "--engine-smoke-test" in sys.argv:
        raise SystemExit(engine_smoke_test(project_root))
    if "--spectator-smoke-test" in sys.argv:
        raise SystemExit(spectator_smoke_test(project_root))
    run(project_root)
