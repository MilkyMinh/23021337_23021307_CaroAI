"""Benchmark Minimax và Alpha-Beta trên các trạng thái kiểm thử.

Chạy từ thư mục gốc project:
    python source_code/benchmark_caro.py
"""

from __future__ import annotations

import csv
import os
from typing import Callable

try:
    from source_code.carogame import AI, BOARD_SIZE, EMPTY, HUMAN, CaroEngine
except ModuleNotFoundError:  # khi chạy trực tiếp trong source_code
    from carogame import AI, BOARD_SIZE, EMPTY, HUMAN, CaroEngine


def empty_board() -> list[list[int]]:
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def board_to_text(board: list[list[int]]) -> str:
    symbol = {EMPTY: ".", HUMAN: "X", AI: "O"}
    return "\n".join(" ".join(symbol[cell] for cell in row) for row in board)


def state_start() -> list[list[int]]:
    return empty_board()


def state_midgame() -> list[list[int]]:
    b = empty_board()
    for r, c, p in [
        (4, 4, AI), (4, 5, HUMAN), (5, 4, AI), (5, 5, HUMAN),
        (3, 4, AI), (6, 5, HUMAN), (5, 3, AI), (4, 6, HUMAN),
    ]:
        b[r][c] = p
    return b


def state_ai_can_win() -> list[list[int]]:
    b = empty_board()
    b[4][2] = AI
    b[4][3] = AI
    b[4][4] = AI
    b[5][4] = HUMAN
    b[6][4] = HUMAN
    return b


def state_human_threat() -> list[list[int]]:
    b = empty_board()
    b[5][3] = HUMAN
    b[5][4] = HUMAN
    b[5][5] = HUMAN
    b[5][6] = AI  # chỉ còn ô (5,2) là điểm chặn thắng ngay
    b[4][4] = AI
    return b


def state_both_attack() -> list[list[int]]:
    b = empty_board()
    # AI có thế ngang 2 và chéo 2
    b[4][3] = AI
    b[4][4] = AI
    b[3][3] = AI
    b[5][5] = AI
    # Human có thế dọc 3 cần được quan tâm
    b[2][6] = HUMAN
    b[3][6] = HUMAN
    b[4][6] = HUMAN
    b[5][2] = HUMAN
    return b


def state_many_branches() -> list[list[int]]:
    b = empty_board()
    for r, c, p in [
        (3, 3, HUMAN), (3, 4, AI), (3, 5, HUMAN), (3, 6, AI),
        (4, 3, AI), (4, 5, HUMAN), (4, 6, AI),
        (5, 3, HUMAN), (5, 4, AI), (5, 6, HUMAN),
        (6, 3, AI), (6, 4, HUMAN), (6, 5, AI), (6, 6, HUMAN),
    ]:
        b[r][c] = p
    return b


STATES: list[tuple[str, Callable[[], list[list[int]]]]] = [
    ("Đầu ván", state_start),
    ("Giữa ván", state_midgame),
    ("AI có thể thắng ngay", state_ai_can_win),
    ("Human sắp thắng - AI cần chặn", state_human_threat),
    ("Hai bên đều có cơ hội tấn công", state_both_attack),
    ("Nhiều nhánh hợp lệ", state_many_branches),
]


def run_benchmark(depths: tuple[int, ...] = (1, 2, 3), time_limit: float = 5.0) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for state_name, factory in STATES:
        board = factory()
        for depth in depths:
            per_alg = []
            for algorithm in ("minimax", "alphabeta"):
                engine = CaroEngine()
                score, move = engine.find_best_move(
                    board,
                    max_depth=depth,
                    time_limit=time_limit,
                    algorithm=algorithm,
                    use_tactical_checks=False,
                )
                result = engine.last_result
                row = {
                    "state": state_name,
                    "depth": depth,
                    "algorithm": algorithm,
                    "move": move,
                    "score": round(score, 2) if isinstance(score, float) else score,
                    "nodes": result.nodes_visited if result else engine.nodes_visited,
                    "time_seconds": round(result.elapsed_seconds, 6) if result else None,
                    "timed_out": result.timed_out if result else False,
                }
                rows.append(row)
                per_alg.append(row)

            # bổ sung chỉ số giảm nhánh cho cặp cùng trạng thái/cùng độ sâu
            mini, ab = per_alg
            reduction = 0.0
            if mini["nodes"]:
                reduction = 100.0 * (mini["nodes"] - ab["nodes"]) / mini["nodes"]
            mini["ab_reduction_percent"] = ""
            ab["ab_reduction_percent"] = round(reduction, 2)
            mini["same_move_as_other"] = mini["move"] == ab["move"]
            ab["same_move_as_other"] = mini["move"] == ab["move"]
    return rows


def main() -> None:
    rows = run_benchmark()
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "state", "depth", "algorithm", "move", "score", "nodes", "time_seconds",
                "timed_out", "same_move_as_other", "ab_reduction_percent",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Đã ghi kết quả benchmark vào: {csv_path}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
