import sys
from pathlib import Path

from gomoku.app import run
from gomoku.engine import RapfiEngine


def engine_smoke_test(project_root: Path) -> int:
    """Exercise the engine after freezing, including bundled asset extraction."""
    engine = RapfiEngine(project_root / "engine" / "pbrain-rapfi-windows-sse.exe")
    try:
        move = engine.best_move([], time_ms=300, max_depth=8)
        return 0 if move == (7, 7) else 2
    finally:
        engine.close()


if __name__ == "__main__":
    # PyInstaller extracts bundled engine assets to _MEIPASS at runtime.
    project_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    if "--engine-smoke-test" in sys.argv:
        raise SystemExit(engine_smoke_test(project_root))
    run(project_root)
