# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Rapfi subprocess adapter using the Gomocup/Yixin protocol."""

from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Iterable

from .game import Move


MOVE_PATTERN = re.compile(r"^(\d+)\s*,\s*(\d+)$")


class RapfiError(RuntimeError):
    pass


def parse_move(line: str, board_size: int = 15) -> tuple[int, int] | None:
    match = MOVE_PATTERN.fullmatch(line.strip())
    if not match:
        return None
    x, y = int(match.group(1)), int(match.group(2))
    if 0 <= x < board_size and 0 <= y < board_size:
        return x, y
    return None


class RapfiEngine:
    """Owns one Rapfi process and serializes search requests."""

    def __init__(self, executable: Path, board_size: int = 15) -> None:
        self.executable = Path(executable).resolve()
        self.board_size = board_size
        self._process: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self.executable.is_file()

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            return
        if not self.available:
            raise RapfiError(f"找不到 Rapfi 引擎：{self.executable}")

        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW

        self._lines = queue.Queue()
        try:
            self._process = subprocess.Popen(
                [str(self.executable)],
                cwd=str(self.executable.parent),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise RapfiError(f"无法启动 Rapfi：{exc}") from exc

        threading.Thread(target=self._read_output, daemon=True).start()
        self._send(f"START {self.board_size}")
        self._wait_for_ok(timeout=12.0)

    def best_move(
        self,
        moves: Iterable[Move],
        *,
        time_ms: int = 1200,
        max_depth: int = 24,
    ) -> tuple[int, int]:
        with self._lock:
            self.start()
            snapshot = list(moves)
            thread_count = max(1, min(4, os.cpu_count() or 1))
            self._send("INFO RULE 0")
            self._send(f"INFO THREAD_NUM {thread_count}")
            self._send("INFO HASH_SIZE 65536")
            self._send(f"INFO TIMEOUT_TURN {max(100, time_ms)}")
            self._send(f"INFO TIMEOUT_MATCH {max(1000, time_ms * 30)}")
            self._send(f"INFO TIME_LEFT {max(1000, time_ms * 30)}")
            self._send(f"INFO MAX_DEPTH {max(2, max_depth)}")
            self._send("INFO SHOW_DETAIL 0")

            parts = ["YXBOARD"]
            parts.extend(f"{m.x},{m.y},{int(m.stone)}" for m in snapshot)
            parts.append("DONE")
            self._send(" ".join(parts))
            self._send("YXNBEST 1")

            deadline_seconds = max(8.0, time_ms / 1000 + 8.0)
            while True:
                line = self._next_line(deadline_seconds)
                move = parse_move(line, self.board_size)
                if move is not None:
                    return move
                upper = line.upper()
                if upper.startswith("ERROR") or upper.startswith("UNKNOWN"):
                    raise RapfiError(f"Rapfi 返回错误：{line}")

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            try:
                self._send("YXSTOP")
            except RapfiError:
                pass

    def close(self) -> None:
        process, self._process = self._process, None
        if not process:
            return
        if process.poll() is None:
            try:
                if process.stdin:
                    process.stdin.write("END\n")
                    process.stdin.flush()
                process.wait(timeout=1.0)
            except (OSError, subprocess.TimeoutExpired):
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()

    def _read_output(self) -> None:
        process = self._process
        if not process or not process.stdout:
            return
        try:
            for line in process.stdout:
                self._lines.put(line.strip())
        finally:
            self._lines.put(None)

    def _send(self, command: str) -> None:
        process = self._process
        if not process or process.poll() is not None or not process.stdin:
            raise RapfiError("Rapfi 引擎未运行")
        try:
            process.stdin.write(command + "\n")
            process.stdin.flush()
        except OSError as exc:
            raise RapfiError("与 Rapfi 的连接已中断") from exc

    def _next_line(self, timeout: float) -> str:
        try:
            line = self._lines.get(timeout=timeout)
        except queue.Empty as exc:
            raise RapfiError("Rapfi 思考超时") from exc
        if line is None:
            raise RapfiError("Rapfi 引擎意外退出")
        return line

    def _wait_for_ok(self, timeout: float) -> None:
        while True:
            line = self._next_line(timeout)
            if line.upper() == "OK":
                return
            if line.upper().startswith("ERROR"):
                raise RapfiError(f"Rapfi 初始化失败：{line}")
