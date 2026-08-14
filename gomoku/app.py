# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Tk desktop interface for Rapfi Gomoku."""

from __future__ import annotations

import math
import random
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .engine import RapfiEngine, RapfiError
from .game import Board, InvalidMove, Stone


BG = "#101416"
PANEL = "#191E21"
PANEL_ALT = "#22282C"
TEXT = "#F4F0E8"
MUTED = "#9DA5A8"
ACCENT = "#E8AF4A"
ACCENT_DARK = "#B87E21"
RED = "#E66A5C"
GREEN = "#6FCB91"
BOARD_LIGHT = "#D9A85D"
BOARD_DARK = "#B87934"


class GomokuApp:
    SIZE = 15

    def __init__(self, root: tk.Tk, project_root: Path) -> None:
        self.root = root
        self.project_root = project_root
        self.board = Board(self.SIZE)
        self.mode = "single"
        self.human_color = Stone.BLACK
        self.thinking = False
        self.hover: tuple[int, int] | None = None
        self.search_token = 0
        self.started_at = time.monotonic()
        self.engine = RapfiEngine(
            project_root / "engine" / "pbrain-rapfi-windows-sse.exe", self.SIZE
        )

        self.root.title("斗弈 · Rapfi 五子棋")
        self.root.geometry("1120x780")
        self.root.minsize(900, 660)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self._draw_board()
        self._update_status()

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg=BG, height=82)
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(22, 8))
        header.grid_columnconfigure(1, weight=1)

        logo = tk.Canvas(header, width=46, height=46, bg=BG, highlightthickness=0)
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 14))
        logo.create_oval(3, 3, 26, 26, fill="#0A0B0C", outline="#343A3E")
        logo.create_oval(20, 20, 43, 43, fill="#F4F0E8", outline="#CED1D0")
        logo.create_oval(29, 5, 39, 15, fill=ACCENT, outline="")

        tk.Label(
            header,
            text="斗弈",
            bg=BG,
            fg=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            header,
            text="RAPFI GOMOKU",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 8, "bold"),
        ).grid(row=1, column=1, sticky="nw")

        self.engine_badge = tk.Label(
            header,
            text="●  RAPFI 内置引擎",
            bg=PANEL,
            fg=GREEN if self.engine.available else RED,
            padx=14,
            pady=8,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.engine_badge.grid(row=0, column=2, rowspan=2, sticky="e")

        content = tk.Frame(self.root, bg=BG)
        content.grid(row=1, column=0, sticky="nsew", padx=34, pady=(4, 28))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        board_card = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground="#2A3034")
        board_card.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        board_card.grid_columnconfigure(0, weight=1)
        board_card.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            board_card,
            bg=PANEL,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.canvas.bind("<Configure>", lambda _event: self._draw_board())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)

        side = tk.Frame(content, bg=PANEL, width=286, highlightthickness=1, highlightbackground="#2A3034")
        side.grid(row=0, column=1, sticky="ns")
        side.grid_propagate(False)

        self._section_label(side, "对战模式").pack(anchor="w", padx=20, pady=(22, 10))
        mode_row = tk.Frame(side, bg=PANEL_ALT)
        mode_row.pack(fill="x", padx=20)
        self.single_button = self._segment_button(mode_row, "单人对战", lambda: self._set_mode("single"))
        self.single_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.double_button = self._segment_button(mode_row, "双人对战", lambda: self._set_mode("double"))
        self.double_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)

        self.color_group = tk.Frame(side, bg=PANEL)
        self.color_group.pack(fill="x", padx=20, pady=(14, 0))
        tk.Label(
            self.color_group,
            text="你的棋色",
            bg=PANEL,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left")
        self.black_button = self._small_button(self.color_group, "● 黑", lambda: self._set_human_color(Stone.BLACK))
        self.black_button.pack(side="right", padx=(6, 0))
        self.white_button = self._small_button(self.color_group, "○ 白", lambda: self._set_human_color(Stone.WHITE))
        self.white_button.pack(side="right")

        divider = tk.Frame(side, bg="#2B3236", height=1)
        divider.pack(fill="x", padx=20, pady=20)

        self.turn_label = tk.Label(
            side,
            text="黑方落子",
            bg=PANEL,
            fg=TEXT,
            font=("Microsoft YaHei UI", 17, "bold"),
        )
        self.turn_label.pack(anchor="w", padx=20)
        self.status_label = tk.Label(
            side,
            text="轮到你了",
            bg=PANEL,
            fg=ACCENT,
            font=("Microsoft YaHei UI", 10),
        )
        self.status_label.pack(anchor="w", padx=20, pady=(4, 14))

        info_row = tk.Frame(side, bg=PANEL_ALT)
        info_row.pack(fill="x", padx=20, pady=(0, 18))
        self.move_count_label = self._metric(info_row, "手数", "0")
        self.move_count_label.master.pack(side="left", fill="x", expand=True, padx=(0, 1))
        self.time_label = self._metric(info_row, "用时", "00:00")
        self.time_label.master.pack(side="left", fill="x", expand=True, padx=(1, 0))

        self._section_label(side, "棋谱").pack(anchor="w", padx=20, pady=(0, 8))
        self.moves_text = tk.Text(
            side,
            height=9,
            bg="#14191B",
            fg="#D5D9D8",
            insertbackground=TEXT,
            selectbackground="#3B454A",
            relief="flat",
            padx=11,
            pady=8,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
        )
        self.moves_text.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        controls = tk.Frame(side, bg=PANEL)
        controls.pack(fill="x", padx=20, pady=(0, 20))
        self.new_button = self._action_button(controls, "新对局", self.new_game, primary=True)
        self.new_button.pack(fill="x", pady=(0, 8))
        self.undo_button = self._action_button(controls, "悔棋", self.undo)
        self.undo_button.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.center_button = self._action_button(controls, "回到中心", self._center_hint)
        self.center_button.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._refresh_mode_buttons()
        self.root.after(500, self._tick)

    def _section_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text.upper(),
            bg=PANEL,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def _segment_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=8,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def _small_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=PANEL_ALT,
            fg=TEXT,
            activebackground="#343C40",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=9,
            pady=4,
            font=("Microsoft YaHei UI", 8, "bold"),
        )

    def _action_button(self, parent: tk.Widget, text: str, command, primary: bool = False) -> tk.Button:
        bg = ACCENT if primary else PANEL_ALT
        fg = "#17130D" if primary else TEXT
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=ACCENT_DARK if primary else "#343C40",
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=9,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def _metric(self, parent: tk.Widget, title: str, value: str) -> tk.Label:
        frame = tk.Frame(parent, bg=PANEL_ALT)
        tk.Label(frame, text=title, bg=PANEL_ALT, fg=MUTED, font=("Microsoft YaHei UI", 8)).pack(pady=(8, 0))
        label = tk.Label(frame, text=value, bg=PANEL_ALT, fg=TEXT, font=("Segoe UI", 13, "bold"))
        label.pack(pady=(0, 8))
        return label

    def _set_mode(self, mode: str) -> None:
        if mode == self.mode:
            return
        self.mode = mode
        self._refresh_mode_buttons()
        self.new_game()

    def _set_human_color(self, color: Stone) -> None:
        if color == self.human_color:
            return
        self.human_color = color
        self._refresh_mode_buttons()
        self.new_game()

    def _refresh_mode_buttons(self) -> None:
        selected = {"bg": ACCENT, "fg": "#17130D", "activebackground": ACCENT_DARK}
        idle = {"bg": PANEL_ALT, "fg": MUTED, "activebackground": "#343C40"}
        self.single_button.configure(**(selected if self.mode == "single" else idle))
        self.double_button.configure(**(selected if self.mode == "double" else idle))
        self.black_button.configure(fg=ACCENT if self.human_color is Stone.BLACK else TEXT)
        self.white_button.configure(fg=ACCENT if self.human_color is Stone.WHITE else TEXT)
        if self.mode == "single":
            self.color_group.pack(fill="x", padx=20, pady=(14, 0), after=self.single_button.master)
        else:
            self.color_group.pack_forget()

    def new_game(self) -> None:
        self.search_token += 1
        if self.thinking:
            self.engine.stop()
        self.thinking = False
        self.board.clear()
        self.hover = None
        self.started_at = time.monotonic()
        self._draw_board()
        self._update_status()
        if self.mode == "single" and self.human_color is Stone.WHITE:
            self.root.after(180, self._request_ai_move)

    def undo(self) -> None:
        if not self.board.moves:
            return
        self.search_token += 1
        was_thinking = self.thinking
        if was_thinking:
            self.engine.stop()
        self.thinking = False
        count = 1 if self.mode == "double" or was_thinking else 2
        self.board.undo(count)
        self._draw_board()
        self._update_status()
        if self.mode == "single" and self.board.current_player is not self.human_color:
            self.root.after(120, self._request_ai_move)

    def _on_click(self, event: tk.Event) -> None:
        if self.thinking or self.board.result.finished:
            return
        if self.mode == "single" and self.board.current_player is not self.human_color:
            return
        point = self._event_to_point(event.x, event.y)
        if point is None:
            return
        try:
            self.board.place(*point)
        except InvalidMove:
            return
        self._draw_board()
        self._update_status()
        if self.mode == "single" and not self.board.result.finished:
            self.root.after(140, self._request_ai_move)

    def _request_ai_move(self) -> None:
        if (
            self.mode != "single"
            or self.board.result.finished
            or self.board.current_player is self.human_color
            or self.thinking
        ):
            return
        if not self.engine.available:
            messagebox.showerror("Rapfi 不可用", "内置引擎文件缺失，请重新下载完整项目。")
            return

        self.thinking = True
        self.search_token += 1
        token = self.search_token
        snapshot = list(self.board.moves)
        self._update_status()

        def think() -> None:
            try:
                move = self.engine.best_move(snapshot, time_ms=1100, max_depth=24)
                self.root.after(0, lambda: self._finish_ai_move(token, move, None))
            except Exception as exc:  # UI boundary: display a friendly engine error.
                self.root.after(0, lambda: self._finish_ai_move(token, None, exc))

        threading.Thread(target=think, name="rapfi-search", daemon=True).start()

    def _finish_ai_move(
        self,
        token: int,
        move: tuple[int, int] | None,
        error: Exception | None,
    ) -> None:
        if token != self.search_token:
            return
        self.thinking = False
        if error is not None:
            self._update_status()
            messagebox.showerror("Rapfi 引擎错误", str(error))
            return
        if move is None:
            return
        try:
            self.board.place(*move)
        except InvalidMove as exc:
            messagebox.showerror("Rapfi 返回非法落点", f"{move}: {exc}")
            return
        self._draw_board()
        self._update_status()

    def _board_geometry(self) -> tuple[float, float, float]:
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        side = min(width, height) - 54
        cell = side / (self.SIZE - 1)
        left = (width - side) / 2
        top = (height - side) / 2
        return left, top, cell

    def _draw_board(self) -> None:
        if not hasattr(self, "canvas"):
            return
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 200)
        left, top, cell = self._board_geometry()
        right = left + cell * (self.SIZE - 1)
        bottom = top + cell * (self.SIZE - 1)
        pad = cell * 0.72

        canvas.create_rectangle(
            left - pad + 5,
            top - pad + 7,
            right + pad + 5,
            bottom + pad + 7,
            fill="#0A0C0D",
            outline="",
        )
        canvas.create_rectangle(
            left - pad,
            top - pad,
            right + pad,
            bottom + pad,
            fill=BOARD_LIGHT,
            outline=BOARD_DARK,
            width=2,
        )

        for stripe in range(14):
            y = top - pad + (stripe + 0.5) * ((bottom - top + pad * 2) / 14)
            color = "#D39B50" if stripe % 2 else "#DCAE65"
            canvas.create_line(left - pad, y, right + pad, y, fill=color, width=1)

        line_color = "#68451F"
        for index in range(self.SIZE):
            pos = index * cell
            canvas.create_line(left, top + pos, right, top + pos, fill=line_color, width=1)
            canvas.create_line(left + pos, top, left + pos, bottom, fill=line_color, width=1)

        stars = ((3, 3), (11, 3), (7, 7), (3, 11), (11, 11))
        star_radius = max(2.2, cell * 0.085)
        for x, y in stars:
            cx, cy = left + x * cell, top + y * cell
            canvas.create_oval(cx - star_radius, cy - star_radius, cx + star_radius, cy + star_radius, fill=line_color, outline="")

        label_font = ("Segoe UI", max(7, int(cell * 0.25)), "bold")
        for index in range(self.SIZE):
            canvas.create_text(left + index * cell, top - pad * 0.62, text=chr(65 + index), fill="#6E4A25", font=label_font)
            canvas.create_text(left - pad * 0.62, top + index * cell, text=str(self.SIZE - index), fill="#6E4A25", font=label_font)

        if self.hover and not self.thinking and not self.board.result.finished:
            x, y = self.hover
            if self.board.at(x, y) is Stone.EMPTY:
                cx, cy = left + x * cell, top + y * cell
                radius = cell * 0.39
                fill = "#282828" if self.board.current_player is Stone.BLACK else "#F3EEE5"
                canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=fill, outline="", stipple="gray50")

        for index, move in enumerate(self.board.moves, start=1):
            self._draw_stone(move.x, move.y, move.stone, index, left, top, cell)

        if self.board.result.winning_line:
            first = self.board.result.winning_line[0]
            last = self.board.result.winning_line[-1]
            canvas.create_line(
                left + first[0] * cell,
                top + first[1] * cell,
                left + last[0] * cell,
                top + last[1] * cell,
                fill=RED,
                width=max(3, int(cell * 0.11)),
                capstyle="round",
            )

    def _draw_stone(self, x: int, y: int, stone: Stone, number: int, left: float, top: float, cell: float) -> None:
        cx, cy = left + x * cell, top + y * cell
        radius = cell * 0.42
        self.canvas.create_oval(cx - radius + 2, cy - radius + 3, cx + radius + 3, cy + radius + 4, fill="#745126", outline="", stipple="gray50")
        if stone is Stone.BLACK:
            colors = ("#090A0B", "#151719", "#272A2C")
            outline = "#060708"
            number_color = "#D9D5CD"
        else:
            colors = ("#C9C8C4", "#E5E2DC", "#FAF8F2")
            outline = "#A9A7A2"
            number_color = "#4C4D4E"
        for idx, color in enumerate(colors):
            inset = idx * radius * 0.15
            self.canvas.create_oval(cx - radius + inset, cy - radius + inset, cx + radius - inset, cy + radius - inset, fill=color, outline=outline if idx == 0 else "")
        highlight_r = radius * 0.13
        self.canvas.create_oval(cx - radius * 0.45 - highlight_r, cy - radius * 0.45 - highlight_r, cx - radius * 0.45 + highlight_r, cy - radius * 0.45 + highlight_r, fill="#606365" if stone is Stone.BLACK else "#FFFFFF", outline="")

        if number == len(self.board.moves):
            marker = max(2, cell * 0.07)
            self.canvas.create_rectangle(cx - marker, cy - marker, cx + marker, cy + marker, fill=RED, outline="")
        elif cell >= 27:
            self.canvas.create_text(cx, cy, text=str(number), fill=number_color, font=("Segoe UI", max(7, int(cell * 0.22)), "bold"))

    def _event_to_point(self, event_x: int, event_y: int) -> tuple[int, int] | None:
        left, top, cell = self._board_geometry()
        x = round((event_x - left) / cell)
        y = round((event_y - top) / cell)
        if not self.board.inside(x, y):
            return None
        if math.hypot(event_x - (left + x * cell), event_y - (top + y * cell)) > cell * 0.48:
            return None
        return x, y

    def _on_motion(self, event: tk.Event) -> None:
        point = self._event_to_point(event.x, event.y)
        if point != self.hover:
            self.hover = point
            self._draw_board()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.hover is not None:
            self.hover = None
            self._draw_board()

    def _update_status(self) -> None:
        result = self.board.result
        if result.winner is not Stone.EMPTY:
            name = "黑方" if result.winner is Stone.BLACK else "白方"
            self.turn_label.configure(text=f"{name}获胜")
            self.status_label.configure(text="五子连珠 · 对局结束", fg=GREEN)
        elif result.draw:
            self.turn_label.configure(text="和棋")
            self.status_label.configure(text="棋盘已满", fg=MUTED)
        elif self.thinking:
            self.turn_label.configure(text="Rapfi 思考中")
            self.status_label.configure(text="正在计算最佳落点…", fg=ACCENT)
        else:
            current = "黑方" if self.board.current_player is Stone.BLACK else "白方"
            self.turn_label.configure(text=f"{current}落子")
            if self.mode == "single":
                text = "轮到你了" if self.board.current_player is self.human_color else "等待 Rapfi"
            else:
                text = "本地双人对战"
            self.status_label.configure(text=text, fg=ACCENT)

        self.move_count_label.configure(text=str(len(self.board.moves)))
        lines = []
        for idx in range(0, len(self.board.moves), 2):
            black = self.board.moves[idx]
            black_pos = f"{chr(65 + black.x)}{self.SIZE - black.y}"
            white_pos = "—"
            if idx + 1 < len(self.board.moves):
                white = self.board.moves[idx + 1]
                white_pos = f"{chr(65 + white.x)}{self.SIZE - white.y}"
            lines.append(f"{idx // 2 + 1:>2}.  ● {black_pos:<4}   ○ {white_pos}")
        self.moves_text.configure(state="normal")
        self.moves_text.delete("1.0", "end")
        self.moves_text.insert("1.0", "\n".join(lines) if lines else "落子后将在这里生成棋谱")
        self.moves_text.see("end")
        self.moves_text.configure(state="disabled")

    def _tick(self) -> None:
        elapsed = int(time.monotonic() - self.started_at)
        self.time_label.configure(text=f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.root.after(500, self._tick)

    def _center_hint(self) -> None:
        self.hover = (self.SIZE // 2, self.SIZE // 2)
        self._draw_board()

    def on_close(self) -> None:
        self.search_token += 1
        self.engine.close()
        self.root.destroy()


def run(project_root: Path) -> None:
    root = tk.Tk()
    GomokuApp(root, project_root)
    root.mainloop()
