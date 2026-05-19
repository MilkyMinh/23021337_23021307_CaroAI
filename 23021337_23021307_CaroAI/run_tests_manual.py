from source_code.carogame import CaroEngine, BOARD_SIZE, EMPTY, HUMAN, AI
import sys


def empty_board():
    return [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]


failed = 0

engine = CaroEngine()
b = empty_board()
r = 4
for c in range(2, 6):
    b[r][c] = HUMAN
if engine.check_winner(b, HUMAN):
    print("TEST 1 PASS: winner detected for HUMAN")
else:
    print("TEST 1 FAIL: winner not detected for HUMAN")
    failed += 1

if not engine.check_winner(b, AI):
    print("TEST 1 PASS: AI not winning")
else:
    print("TEST 1 FAIL: AI incorrectly winning")
    failed += 1

engine = CaroEngine()
b = empty_board()
r = 5
b[r][3] = HUMAN
b[r][4] = HUMAN
b[r][5] = HUMAN
b[r][6] = AI
score, move = engine.find_best_move(b, max_depth=3, time_limit=1.0, algorithm="alphabeta")
print("AI returned move:", move, "score:", score)
if move == (r, 2):
    print("TEST 2 PASS: AI blocked the remaining winning flank")
else:
    print("TEST 2 FAIL: expected", (r, 2), "got", move)
    failed += 1

engine_m = CaroEngine()
engine_ab = CaroEngine()
b = empty_board()
b[4][4] = AI
b[4][5] = AI
b[5][4] = HUMAN
b[6][4] = HUMAN
score_m, move_m = engine_m.find_best_move(b, max_depth=2, time_limit=2.0, algorithm="minimax", use_tactical_checks=False)
score_ab, move_ab = engine_ab.find_best_move(b, max_depth=2, time_limit=2.0, algorithm="alphabeta", use_tactical_checks=False)
print("Minimax:", move_m, score_m, engine_m.last_result.nodes_visited, "nodes")
print("Alpha-Beta:", move_ab, score_ab, engine_ab.last_result.nodes_visited, "nodes")
if move_m == move_ab and score_m == score_ab:
    print("TEST 3 PASS: Minimax and Alpha-Beta match on same depth/evaluation")
else:
    print("TEST 3 FAIL: algorithms do not match")
    failed += 1

if failed:
    print(f"{failed} tests failed")
    sys.exit(2)
print("All manual tests passed")
sys.exit(0)
