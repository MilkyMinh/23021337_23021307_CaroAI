"""Game Caro 4 quân liên tiếp với AI Minimax và Alpha-Beta.

- Người chơi: X / HUMAN = 1
- Máy tính: O / AI = 2
- Ô trống: . / EMPTY = 0
- Luật thắng: có 4 quân liên tiếp theo ngang, dọc hoặc chéo.
- Không xét luật chặn hai đầu.

Chạy giao diện: python source_code/carogame.py
Chạy test:      python -m pytest tests/test_engine.py
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Iterable, Optional

# -------------------------------------------------------------------
# CẤU HÌNH THEO ĐỀ BÀI
# -------------------------------------------------------------------
BOARD_SIZE = 10  # tối thiểu 9x9, dùng 10x10 để giao diện dễ nhìn
EMPTY = 0
HUMAN = 1  # X - người chơi, vai trò MIN trong cây tìm kiếm
AI = 2     # O - máy tính, vai trò MAX trong cây tìm kiếm
DRAW = 3

WIN_LENGTH = 4
WIN_SCORE = 10**9
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
MAX_CANDIDATE_MOVES = 18  # giới hạn số nhánh sau khi sắp xếp để chạy được ở độ sâu 3-4

# Điểm cửa sổ 4 ô. Người chơi được phạt mạnh hơn một chút để AI ưu tiên chặn.
AI_WINDOW_SCORE = {1: 15, 2: 250, 3: 50_000, 4: WIN_SCORE}
HUMAN_WINDOW_SCORE = {1: 18, 2: 300, 3: 80_000, 4: WIN_SCORE}


@dataclass
class SearchResult:
    algorithm: str
    depth: int
    score: float
    move: Optional[tuple[int, int]]
    nodes_visited: int
    elapsed_seconds: float
    timed_out: bool = False


class CaroEngine:
    """Phần lõi xử lý luật chơi và thuật toán AI."""

    def __init__(self) -> None:
        self.nodes_visited = 0
        self.start_time = 0.0
        self.time_limit: Optional[float] = None
        self.deadline: Optional[float] = None
        self.timed_out = False
        self.last_result: Optional[SearchResult] = None

    # --------------------------- Luật chơi ---------------------------
    def new_board(self) -> list[list[int]]:
        return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def is_valid_move(self, board: list[list[int]], row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and board[row][col] == EMPTY

    def is_board_full(self, board: list[list[int]]) -> bool:
        return all(cell != EMPTY for row in board for cell in row)

    def check_winner(self, board: list[list[int]], player: int) -> bool:
        """Trả về True nếu player có ít nhất 4 quân liên tiếp."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != player:
                    continue
                for dr, dc in DIRECTIONS:
                    count = 1
                    for step in range(1, WIN_LENGTH):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                            count += 1
                        else:
                            break
                    if count >= WIN_LENGTH:
                        return True
        return False

    def get_game_result(self, board: list[list[int]]) -> Optional[int]:
        """AI/HUMAN nếu có người thắng, DRAW nếu hòa, None nếu ván chưa kết thúc."""
        if self.check_winner(board, AI):
            return AI
        if self.check_winner(board, HUMAN):
            return HUMAN
        if self.is_board_full(board):
            return DRAW
        return None

    # ------------------------- Sinh nước đi --------------------------
    def get_valid_moves(self, board: list[list[int]], radius: int = 1) -> list[tuple[int, int]]:
        """Sinh các ô trống gần quân đã đánh để giảm không gian tìm kiếm.

        Nếu bàn cờ còn trống hoàn toàn, AI chọn ô trung tâm.
        """
        occupied = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != EMPTY]
        if not occupied:
            mid = BOARD_SIZE // 2
            return [(mid, mid)]

        moves: set[tuple[int, int]] = set()
        for r, c in occupied:
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    nr, nc = r + dr, c + dc
                    if self.is_valid_move(board, nr, nc):
                        moves.add((nr, nc))

        ordered = self.order_moves(board, list(moves))
        return ordered[:MAX_CANDIDATE_MOVES]

    def order_moves(self, board: list[list[int]], moves: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
        """Sắp xếp nước đi: thắng ngay, chặn thắng ngay, tạo/chặn chuỗi 3, gần trung tâm."""
        center = (BOARD_SIZE - 1) / 2

        def priority(move: tuple[int, int]) -> tuple[float, float]:
            r, c = move

            board[r][c] = AI
            ai_score = self._local_potential(board, r, c, AI)
            ai_win = self.check_winner(board, AI)
            board[r][c] = EMPTY
            if ai_win:
                return (10**12, 0)

            board[r][c] = HUMAN
            human_score = self._local_potential(board, r, c, HUMAN)
            human_win = self.check_winner(board, HUMAN)
            board[r][c] = EMPTY

            block_bonus = 10**11 if human_win else 0
            distance = abs(r - center) + abs(c - center)
            return (block_bonus + ai_score + human_score * 1.2, -distance)

        return sorted(moves, key=priority, reverse=True)

    def _local_potential(self, board: list[list[int]], r: int, c: int, player: int) -> float:
        """Điểm cục bộ dùng riêng cho move ordering, nhẹ hơn evaluate_board."""
        total_score = 0.0
        weight = {1: 15, 2: 250, 3: 50_000, 4: WIN_SCORE}
        for dr, dc in DIRECTIONS:
            count = 1
            open_ends = 0

            nr, nc = r + dr, c + dc
            while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                count += 1
                nr += dr
                nc += dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                open_ends += 1

            nr, nc = r - dr, c - dc
            while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                count += 1
                nr -= dr
                nc -= dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                open_ends += 1

            count = min(count, WIN_LENGTH)
            total_score += weight[count] * (1 + 0.15 * open_ends)
        return total_score

    # ------------------------- Hàm đánh giá --------------------------
    def evaluate_board(self, board: list[list[int]]) -> float:
        result = self.get_game_result(board)
        if result == AI:
            return WIN_SCORE
        if result == HUMAN:
            return -WIN_SCORE
        if result == DRAW:
            return 0

        score = 0.0
        for window in self._iter_windows(board):
            ai_count = window.count(AI)
            human_count = window.count(HUMAN)
            empty_count = window.count(EMPTY)

            # Cửa sổ có cả X và O thì không còn tạo được 4 liên tiếp trong cửa sổ đó.
            if ai_count > 0 and human_count > 0:
                continue
            if ai_count > 0 and human_count == 0:
                score += AI_WINDOW_SCORE[ai_count]
                if empty_count > 0:
                    score += 2 * ai_count  # cộng nhẹ cho khả năng mở rộng
            elif human_count > 0 and ai_count == 0:
                score -= HUMAN_WINDOW_SCORE[human_count]
                if empty_count > 0:
                    score -= 2.5 * human_count

        # Ưu tiên kiểm soát trung tâm ở mức nhỏ, chỉ dùng để phá hòa điểm.
        center = (BOARD_SIZE - 1) / 2
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == EMPTY:
                    continue
                center_bonus = (BOARD_SIZE - (abs(r - center) + abs(c - center))) * 0.2
                score += center_bonus if board[r][c] == AI else -center_bonus
        return score

    def _iter_windows(self, board: list[list[int]]) -> Iterable[list[int]]:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                for dr, dc in DIRECTIONS:
                    cells: list[int] = []
                    for step in range(WIN_LENGTH):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            cells.append(board[nr][nc])
                    if len(cells) == WIN_LENGTH:
                        yield cells

    #Minimax 
    def minimax(self, board: list[list[int]], depth: int, is_max: bool) -> tuple[float, Optional[tuple[int, int]]]:
        self.nodes_visited += 1
        if self._time_is_up():
            return self.evaluate_board(board), None

        result = self.get_game_result(board)
        if result is not None or depth == 0:
            return self.evaluate_board(board), None

        moves = self.get_valid_moves(board)
        best_move: Optional[tuple[int, int]] = None

        if is_max:
            best_score = -math.inf
            for r, c in moves:
                board[r][c] = AI
                score, _ = self.minimax(board, depth - 1, False)
                board[r][c] = EMPTY
                if score > best_score:
                    best_score, best_move = score, (r, c)
                if self.timed_out:
                    break
            return best_score, best_move

        best_score = math.inf
        for r, c in moves:
            board[r][c] = HUMAN
            score, _ = self.minimax(board, depth - 1, True)
            board[r][c] = EMPTY
            if score < best_score:
                best_score, best_move = score, (r, c)
            if self.timed_out:
                break
        return best_score, best_move

    #Alpha-Beta 
    def alpha_beta(
        self,
        board: list[list[int]],
        depth: int,
        alpha: float,
        beta: float,
        is_max: bool,
    ) -> tuple[float, Optional[tuple[int, int]]]:
        self.nodes_visited += 1
        if self._time_is_up():
            return self.evaluate_board(board), None

        result = self.get_game_result(board)
        if result is not None or depth == 0:
            return self.evaluate_board(board), None

        moves = self.get_valid_moves(board)
        best_move: Optional[tuple[int, int]] = None

        if is_max:
            best_score = -math.inf
            for r, c in moves:
                board[r][c] = AI
                score, _ = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board[r][c] = EMPTY
                if score > best_score:
                    best_score, best_move = score, (r, c)
                alpha = max(alpha, best_score)
                if self.timed_out or beta <= alpha:
                    break
            return best_score, best_move

        best_score = math.inf
        for r, c in moves:
            board[r][c] = HUMAN
            score, _ = self.alpha_beta(board, depth - 1, alpha, beta, True)
            board[r][c] = EMPTY
            if score < best_score:
                best_score, best_move = score, (r, c)
            beta = min(beta, best_score)
            if self.timed_out or beta <= alpha:
                break
        return best_score, best_move

    #Chọn nước đi
    def find_best_move(
        self,
        board: list[list[int]],
        max_depth: int = 3,
        time_limit: Optional[float] = 2.5,
        algorithm: str = "alphabeta",
        use_tactical_checks: bool = True,
    ) -> tuple[float, Optional[tuple[int, int]]]:
        """Trả về (score, move) để tương thích với file test cũ.

        algorithm: "minimax" hoặc "alphabeta".
        """
        self.start_time = time.perf_counter()
        self.time_limit = time_limit
        self.deadline = self.start_time + time_limit if time_limit is not None else None
        self.timed_out = False
        self.nodes_visited = 0
        algorithm = algorithm.lower().replace("-", "").replace("_", "")
        if algorithm in {"alpha", "ab"}:
            algorithm = "alphabeta"
        if algorithm not in {"minimax", "alphabeta"}:
            raise ValueError("algorithm phải là 'minimax' hoặc 'alphabeta'")

        if self.get_game_result(board) is not None:
            score, move = self.evaluate_board(board), None
            self._store_result(algorithm, max_depth, score, move)
            return score, move

        #Kiểm tra chiến thuật nhanh dùng khi chơi thật: thắng ngay hoặc chặn thắng ngay.
        if use_tactical_checks:
            immediate_ai = self._immediate_winning_moves(board, AI)
            if immediate_ai:
                score, move = WIN_SCORE, immediate_ai[0]
                self._store_result(algorithm, max_depth, score, move)
                return score, move

            immediate_human = self._immediate_winning_moves(board, HUMAN)
            if len(immediate_human) == 1:
                score, move = -WIN_SCORE // 2, immediate_human[0]
                self._store_result(algorithm, max_depth, score, move)
                return score, move

        if algorithm == "minimax":
            score, move = self.minimax(board, max_depth, True)
        else:
            score, move = self.alpha_beta(board, max_depth, -math.inf, math.inf, True)

        self._store_result(algorithm, max_depth, score, move)
        return score, move

    def _immediate_winning_moves(self, board: list[list[int]], player: int) -> list[tuple[int, int]]:
        moves: list[tuple[int, int]] = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == EMPTY:
                    board[r][c] = player
                    if self.check_winner(board, player):
                        moves.append((r, c))
                    board[r][c] = EMPTY
        return self.order_moves(board, moves)

    def _time_is_up(self) -> bool:
        if self.deadline is not None and time.perf_counter() >= self.deadline:
            self.timed_out = True
            return True
        return False

    def _store_result(self, algorithm: str, depth: int, score: float, move: Optional[tuple[int, int]]) -> None:
        elapsed = time.perf_counter() - self.start_time
        self.last_result = SearchResult(
            algorithm=algorithm,
            depth=depth,
            score=score,
            move=move,
            nodes_visited=self.nodes_visited,
            elapsed_seconds=elapsed,
            timed_out=self.timed_out,
        )



#Giao diện đơn giản

class CaroApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Caro AI - Minimax / Alpha-Beta")
        self.engine = CaroEngine()
        self.board = self.engine.new_board()
        self.first_player_var = tk.StringVar(value="human")
        self.difficulty_var = tk.StringVar(value="Medium")
        self.algorithm_var = tk.StringVar(value="Alpha-Beta")
        #Người dùng chọn trực tiếp độ sâu tìm kiếm thay vì chỉ chọn gián tiếp qua độ khó.
        #Đề bài yêu cầu thử/sử dụng các độ sâu 1, 2, 3 nên giao diện để sẵn các mức này,
        #đồng thời có thêm mức 4 để chạy thử nâng cao nếu máy đủ mạnh.
        self.depth_var = tk.StringVar(value="3")
        self.is_thinking = False
        self.game_over = False
        self.setup_ui()
        self.root.mainloop()

    def setup_ui(self) -> None:
        control_frame = tk.Frame(self.root)
        control_frame.pack(side="right", padx=15, fill="y")

        self.status_label = tk.Label(control_frame, text="Lượt của bạn (X)", font=("Arial", 11, "bold"), fg="blue")
        self.status_label.pack(pady=6)

        tk.Label(control_frame, text="Ai đi trước:", font=("Arial", 10)).pack(pady=(8, 0))
        frame_fp = tk.Frame(control_frame)
        frame_fp.pack(pady=2)
        tk.Radiobutton(frame_fp, text="Bạn", variable=self.first_player_var, value="human").pack(side="left")
        tk.Radiobutton(frame_fp, text="AI", variable=self.first_player_var, value="ai").pack(side="left")

        tk.Label(control_frame, text="Thuật toán AI:", font=("Arial", 10)).pack(pady=(8, 0))
        ttk.Combobox(
            control_frame,
            values=["Minimax", "Alpha-Beta"],
            state="readonly",
            width=12,
            textvariable=self.algorithm_var,
        ).pack(pady=2)

        tk.Label(control_frame, text="Độ sâu tìm kiếm:", font=("Arial", 10)).pack(pady=(8, 0))
        self.depth_menu = ttk.Combobox(
            control_frame,
            values=["1", "2", "3", "4"],
            state="readonly",
            width=12,
            textvariable=self.depth_var,
        )
        self.depth_menu.pack(pady=2)
        self.depth_menu.current(2)

        tk.Label(control_frame, text="Độ khó:", font=("Arial", 10)).pack(pady=(8, 0))
        self.difficulty_menu = ttk.Combobox(
            control_frame,
            values=["Easy", "Medium", "Hard"],
            state="readonly",
            width=12,
            textvariable=self.difficulty_var,
        )
        self.difficulty_menu.pack(pady=2)
        self.difficulty_menu.current(1)

        tk.Button(control_frame, text="New Game", command=self.start_new_game).pack(pady=(8, 10), fill="x")

        self.log_text = tk.Text(control_frame, width=42, height=18, font=("Consolas", 9))
        self.log_text.pack(pady=5)

        self.canvas_size = 500
        self.canvas = tk.Canvas(self.root, width=self.canvas_size, height=self.canvas_size, bg="#F0D9B5")
        self.canvas.pack(side="left", padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.draw_board()

    def draw_board(self) -> None:
        self.canvas.delete("all")
        s = self.canvas_size // BOARD_SIZE
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                self.canvas.create_rectangle(c * s, r * s, (c + 1) * s, (r + 1) * s, outline="#5D4037")
                if self.board[r][c] == HUMAN:
                    self.canvas.create_text(c * s + s / 2, r * s + s / 2, text="X", font=("Arial", 24, "bold"), fill="#1A237E")
                elif self.board[r][c] == AI:
                    self.canvas.create_text(c * s + s / 2, r * s + s / 2, text="O", font=("Arial", 24, "bold"), fill="#B71C1C")

    def handle_click(self, event: tk.Event) -> None:
        if self.is_thinking or self.game_over or self._turn_is_ai():
            return
        s = self.canvas_size // BOARD_SIZE
        c, r = event.x // s, event.y // s
        if not self.engine.is_valid_move(self.board, r, c):
            return

        self.board[r][c] = HUMAN
        self.draw_board()
        if self._show_end_if_needed():
            return
        self._run_ai_async()

    def _turn_is_ai(self) -> bool:
        human_count = sum(row.count(HUMAN) for row in self.board)
        ai_count = sum(row.count(AI) for row in self.board)
        if self.first_player_var.get() == "ai":
            return ai_count <= human_count
        return ai_count < human_count

    def _settings(self) -> tuple[int, float]:
        
        try:
            max_depth = int(self.depth_var.get())
        except ValueError:
            max_depth = 3

        diff = self.difficulty_var.get()
        if diff == "Easy":
            return max_depth, 1.0
        if diff == "Hard":
            return max_depth, 5.0
        return max_depth, 2.5

    def _algorithm_key(self) -> str:
        return "minimax" if self.algorithm_var.get() == "Minimax" else "alphabeta"

    def _run_ai_async(self) -> None:
        self.is_thinking = True
        self.status_label.config(text="AI đang suy nghĩ...", fg="red")
        threading.Thread(target=self.ai_process, daemon=True).start()

    def ai_process(self) -> None:
        max_depth, time_limit = self._settings()
        algorithm = self._algorithm_key()
        score, move = self.engine.find_best_move(
            self.board,
            max_depth=max_depth,
            time_limit=time_limit,
            algorithm=algorithm,
            use_tactical_checks=True,
        )
        result = self.engine.last_result

        def update_ui() -> None:
            if move is not None:
                r, c = move
                self.board[r][c] = AI
                self.draw_board()
                elapsed = result.elapsed_seconds if result else 0.0
                nodes = result.nodes_visited if result else self.engine.nodes_visited
                alg_name = "Minimax" if algorithm == "minimax" else "Alpha-Beta"
                log_msg = (
                    f"> AI ({alg_name}) đánh ({r + 1}, {c + 1})\n"
                    f"  - Độ sâu: {max_depth}\n"
                    f"  - Trạng thái đã xét: {nodes}\n"
                    f"  - Thời gian: {elapsed:.4f}s\n"
                    f"  - Điểm đánh giá: {score}\n\n"
                )
                self.log_text.insert(tk.END, log_msg)
                self.log_text.see(tk.END)

            self.is_thinking = False
            if not self._show_end_if_needed():
                self.status_label.config(text="Lượt của bạn (X)", fg="blue")

        self.root.after(0, update_ui)

    def _show_end_if_needed(self) -> bool:
        result = self.engine.get_game_result(self.board)
        if result is None:
            return False
        self.game_over = True
        if result == HUMAN:
            messagebox.showinfo("Kết thúc", "Bạn thắng!")
        elif result == AI:
            messagebox.showinfo("Kết thúc", "AI thắng!")
        else:
            messagebox.showinfo("Kết thúc", "Ván cờ hòa!")
        self.status_label.config(text="Ván cờ đã kết thúc", fg="black")
        return True

    def reset_game(self) -> None:
        self.board = self.engine.new_board()
        self.is_thinking = False
        self.game_over = False
        self.log_text.delete("1.0", tk.END)
        self.status_label.config(text="Lượt của bạn (X)", fg="blue")
        self.draw_board()

    def start_new_game(self) -> None:
        self.reset_game()
        if self.first_player_var.get() == "ai":
            self._run_ai_async()


if __name__ == "__main__":
    CaroApp()
