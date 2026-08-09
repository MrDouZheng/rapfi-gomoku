"""Pure Gomoku rules and state management."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Stone(IntEnum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2

    @property
    def opponent(self) -> "Stone":
        if self is Stone.BLACK:
            return Stone.WHITE
        if self is Stone.WHITE:
            return Stone.BLACK
        return Stone.EMPTY


@dataclass(frozen=True, slots=True)
class Move:
    x: int
    y: int
    stone: Stone


@dataclass(frozen=True, slots=True)
class GameResult:
    winner: Stone = Stone.EMPTY
    winning_line: tuple[tuple[int, int], ...] = ()
    draw: bool = False

    @property
    def finished(self) -> bool:
        return self.winner is not Stone.EMPTY or self.draw


class InvalidMove(ValueError):
    """Raised when a stone cannot be placed at a requested intersection."""


class Board:
    """A freestyle Gomoku board. Five or more consecutive stones wins."""

    DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))

    def __init__(self, size: int = 15) -> None:
        if size < 5:
            raise ValueError("board size must be at least 5")
        self.size = size
        self.grid: list[list[Stone]] = [
            [Stone.EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.moves: list[Move] = []
        self.result = GameResult()

    @property
    def current_player(self) -> Stone:
        return Stone.BLACK if len(self.moves) % 2 == 0 else Stone.WHITE

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def at(self, x: int, y: int) -> Stone:
        if not self.inside(x, y):
            raise IndexError((x, y))
        return self.grid[y][x]

    def place(self, x: int, y: int) -> Move:
        if self.result.finished:
            raise InvalidMove("game is already finished")
        if not self.inside(x, y):
            raise InvalidMove("position is outside the board")
        if self.grid[y][x] is not Stone.EMPTY:
            raise InvalidMove("position is occupied")

        move = Move(x=x, y=y, stone=self.current_player)
        self.grid[y][x] = move.stone
        self.moves.append(move)
        self.result = self._result_after(move)
        return move

    def undo(self, count: int = 1) -> list[Move]:
        removed: list[Move] = []
        for _ in range(max(0, count)):
            if not self.moves:
                break
            move = self.moves.pop()
            self.grid[move.y][move.x] = Stone.EMPTY
            removed.append(move)
        self.result = GameResult()
        return removed

    def clear(self) -> None:
        self.grid = [[Stone.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.moves.clear()
        self.result = GameResult()

    def engine_position(self) -> list[tuple[int, int, int]]:
        return [(move.x, move.y, int(move.stone)) for move in self.moves]

    def _result_after(self, move: Move) -> GameResult:
        for dx, dy in self.DIRECTIONS:
            line = self._line_through(move.x, move.y, move.stone, dx, dy)
            if len(line) >= 5:
                return GameResult(winner=move.stone, winning_line=tuple(line))
        if len(self.moves) == self.size * self.size:
            return GameResult(draw=True)
        return GameResult()

    def _line_through(
        self, x: int, y: int, stone: Stone, dx: int, dy: int
    ) -> list[tuple[int, int]]:
        start_x, start_y = x, y
        while self.inside(start_x - dx, start_y - dy) and (
            self.grid[start_y - dy][start_x - dx] is stone
        ):
            start_x -= dx
            start_y -= dy

        line: list[tuple[int, int]] = []
        cx, cy = start_x, start_y
        while self.inside(cx, cy) and self.grid[cy][cx] is stone:
            line.append((cx, cy))
            cx += dx
            cy += dy
        return line
