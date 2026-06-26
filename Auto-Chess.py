import chess.engine
import chess.pgn
import os
import time
import asyncio
import pyautogui
import random
import pyscreenshot
from chesstenso import tensorflow_chessbot
from chesstenso import chessboard_finder
from pyclick import HumanClicker
import pytweening
from pyclick.humancurve import HumanCurve

nums = {1:"a", 2:"b", 3:"c", 4:"d", 5:"e", 6:"f", 7:"g", 8:"h"}
def get_uci(board1, board2, who_moved):
    str_board = str(board1).split("\n")
    str_board2 = str(board2).split("\n")
    move = ""
    moved_piece = ""
    flip = False
    leave = False
    if who_moved == "w":
        for i in range(8)[::-1]:
            for x in range(15)[::-1]:
                if str_board[i][x] != str_board2[i][x]:
                    if moved_piece != "" and (str_board[i][x] != moved_piece and str_board2[i][x] != moved_piece):
                        continue
                    if str_board[i][x] == "." and move == "":
                        flip = True
                    moved_piece = str_board2[i][x]if str_board[i][x] == "."else str_board[i][x]
                    move+=str(nums.get(round(x/2)+1))+str(9-(i+1))
                    if len(move) == 4:
                        leave = True
                        break
            if leave:
                break
    else:
        for i in range(8):
            for x in range(15):
                if str_board[i][x] != str_board2[i][x]:
                    if moved_piece != "" and (str_board[i][x] != moved_piece and str_board2[i][x] != moved_piece):
                        continue
                    if str_board[i][x] == "." and move == "":
                        flip = True
                    moved_piece = str_board2[i][x] if str_board[i][x] == "." else str_board[i][x]
                    move += str(nums.get(round(x / 2) + 1)) + str(9 - (i + 1))
                    if len(move) == 4:
                        leave = True
                        break
            if leave:
                break
    if flip:
        move = move[2]+move[3]+move[0]+move[1]
    return move

wait_interval = 0.3 # The wait time between taking screenshots and retrying commands

# --- Stockfish (the engine that double-checks Maia for blunders) ---
stockfish_path = r"Stockfish Path" # The absolute path to the Stockfish (or other UCI) engine
engine_think_time = 1 # <----- The higher this value is the better/slower Stockfish plays and checks

# The Elo Stockfish should play at, used only in "Stockfish only" mode. Set to None for full
# strength. You are also asked for this on startup, which overrides the value set here.
engine_elo = None

# --- Maia (the human-like ML engine) ---
# Maia is a neural network trained on millions of real human games; it predicts the move a human
# of a given rating would actually play instead of the objectively best move. It runs inside lc0.
# Download the weights (maia-1100.pb.gz ... maia-1900.pb.gz) from:
#   https://github.com/CSSLab/maia-chess/tree/master/maia_weights
lc0_path = r"Lc0 Path" # The absolute path to the lc0 executable
maia_weights_dir = r"Maia Weights Dir" # Folder containing the maia-XXXX.pb.gz weight files
maia_rating = 1500 # Which Maia model to use (1100-1900 in steps of 100). Asked for on startup.

# In "Maia + Stockfish" mode, Stockfish overrides Maia's move only when Maia's choice loses at
# least this many centipawns versus Stockfish's best move. This stops obvious blunders while still
# letting Maia play the human-like, slightly sub-optimal moves that make it look human.
blunder_threshold = 150

# Resolve paths to absolute now, because we chdir into ./chesstenso below.
stockfish_path = os.path.abspath(stockfish_path) if os.path.exists(stockfish_path) else stockfish_path
lc0_path = os.path.abspath(lc0_path) if os.path.exists(lc0_path) else lc0_path
maia_weights_dir = os.path.abspath(maia_weights_dir) if os.path.exists(maia_weights_dir) else maia_weights_dir

mode = "maia_sf"   # one of: "maia_sf", "maia", "stockfish"
stockfish = None   # the Stockfish engine handle
maia = None        # the Maia (lc0) engine handle


def configure_elo(eng, elo):
    """Limit the engine's playing strength to the given Elo, if the engine supports it."""
    if elo is None:
        return False
    try:
        eng.configure({"UCI_LimitStrength": True, "UCI_Elo": elo})
        return True
    except chess.engine.EngineError:
        print("Warning: this engine doesn't support Elo limiting (UCI_Elo), "
              "so it will play at full strength.")
        return False


def open_stockfish():
    return chess.engine.SimpleEngine.popen_uci(stockfish_path)


def open_maia(rating):
    weights = os.path.join(maia_weights_dir, f"maia-{rating}.pb.gz")
    return chess.engine.SimpleEngine.popen_uci([lc0_path, f"--weights={weights}"])


def reopen_engines():
    """(Re)start whichever engines the current mode needs. Used at startup and after a crash."""
    global stockfish, maia
    if mode in ("maia_sf", "maia"):
        maia = open_maia(maia_rating)
    if mode in ("maia_sf", "stockfish"):
        stockfish = open_stockfish()
        if mode == "stockfish":
            configure_elo(stockfish, engine_elo)


def cp(score, color):
    """Centipawns of a PovScore from `color`'s point of view (mate counts as +/-100000)."""
    return score.pov(color).score(mate_score=100000)


def pick_move(board):
    """Choose the move to play according to the selected engine mode."""
    if mode == "stockfish":
        return stockfish.play(board, chess.engine.Limit(time=engine_think_time)).move

    # Maia picks a human-like move from a single policy evaluation (no search).
    maia_move = maia.play(board, chess.engine.Limit(nodes=1)).move
    if mode == "maia":
        return maia_move

    # Maia + Stockfish: let Stockfish veto the move only if it is a genuine blunder.
    me = board.turn
    best = stockfish.play(board, chess.engine.Limit(time=engine_think_time),
                          info=chess.engine.INFO_SCORE)
    best_move, best_cp = best.move, cp(best.info["score"], me)
    if maia_move == best_move:
        return maia_move
    board.push(maia_move)
    try:
        if board.is_checkmate():  # Maia found a mate; nothing to second-guess.
            return maia_move
        maia_cp = cp(stockfish.analyse(board, chess.engine.Limit(time=engine_think_time))["score"], me)
    finally:
        board.pop()
    if best_cp - maia_cp >= blunder_threshold:
        print(f"Stockfish veto: Maia's {maia_move} drops {best_cp - maia_cp}cp, "
              f"playing {best_move} instead.")
        return best_move
    return maia_move


os.chdir('chesstenso')
while 1:
    legit = input("Do you want legit mode? (y/n): ")
    if legit!="y" and legit!="n":
        print("Please type y or n.")
        continue
    break

while 1:
    print("Which engine mode?")
    print("  1) Maia + Stockfish double-check (human-like moves, blunders vetoed) [recommended]")
    print("  2) Maia only (pure human-like play)")
    print("  3) Stockfish only (max strength, optional Elo cap)")
    choice = input("Choose 1, 2 or 3: ").strip()
    if choice == "1":
        mode = "maia_sf"
    elif choice == "2":
        mode = "maia"
    elif choice == "3":
        mode = "stockfish"
    else:
        print("Please type 1, 2 or 3.")
        continue
    break

if mode in ("maia_sf", "maia"):
    while 1:
        rating_in = input("Which Maia rating? (1100-1900 in steps of 100, blank for 1500): ").strip()
        if rating_in == "":
            maia_rating = 1500
            break
        if not rating_in.isdigit():
            print("Please enter a number like 1100, 1500 or 1900.")
            continue
        maia_rating = int(rating_in)
        if maia_rating < 1100 or maia_rating > 1900 or maia_rating % 100 != 0:
            print("Maia only has models for 1100, 1200, ... 1900.")
            continue
        break

reopen_engines()

if mode == "stockfish":
    elo_option = stockfish.options.get("UCI_Elo")
    while 1:
        prompt = "What Elo should the bot play at? (leave blank for full strength"
        if elo_option is not None:
            prompt += f", supported: {elo_option.min}-{elo_option.max}"
        elo_in = input(prompt + "): ").strip()
        if elo_in == "":
            engine_elo = None
            break
        if not elo_in.isdigit():
            print("Please enter a whole number, or leave blank for full strength.")
            continue
        engine_elo = int(elo_in)
        if elo_option is not None and (engine_elo < elo_option.min or engine_elo > elo_option.max):
            print(f"This engine only supports an Elo between {elo_option.min} and {elo_option.max}.")
            continue
        break
    if configure_elo(stockfish, engine_elo):
        print(f"Engine strength limited to ~{engine_elo} Elo.")
while 1:
    who = input("Are you playing as white or black?: ")
    if who == "white":
        who = "w"
        other = "b"
        flip = False
        prev_fen = "IDEK"
    elif who == "black":
        who = "b"
        other = "w"
        flip = True
        prev_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    else:
        print("Invalid option given (white/black), please try again.")
        continue
    break

invalid = 0
board = chess.Board()
first_move = True
while True:
    image = pyscreenshot.grab()
    image.save("board.png")
    try:
        result = tensorflow_chessbot.main(img='board.png', active=who, unflip=flip)
        accuracy = result[1]
    except:
        time.sleep(wait_interval)
        continue
    if str(result[0]).split(" ")[0] == prev_fen:
        time.sleep(wait_interval)
        continue

    board1 = chess.Board(result[0])
    if not board1.is_valid():
        if invalid >= 10:
            print(f"Unable to detect a valid board position... Detected board position with {round(accuracy, 2)}% confidence was:")
            print(board1)
            break
        print("Invalid board position detected, retrying...")
        invalid+=1
        time.sleep(wait_interval)
        continue
    invalid = 0

    if not first_move:
        try:
            move_made = get_uci(board, board1, other)
            print("Detected move was: " + move_made)
            board.push_uci(move_made)
            if str(board) != str(board1):
                board = chess.Board(result[0])
        except:
            board = chess.Board(result[0])
    else:
        first_move = False
        board = chess.Board(result[0])

    while 1:
        try:
            move = pick_move(board)
            break
        except asyncio.exceptions.TimeoutError:
            continue
        except chess.engine.EngineTerminatedError:
            reopen_engines()
            continue
    print(f"Detected board position with {round(accuracy, 2)}% confidence:")
    print(board)
    print("Playing Move: " + str(move))
    print()
    try:
        board.push(move)
        prev_fen = str(board.fen().split(" ")[0])
    except:
        print("Looks like I got checkmated, how is that even possible?")
        break

    board_pos = chessboard_finder.main(url=os.path.abspath('board.png'))

    board_width = board_pos[2] - board_pos[0]
    board_height = board_pos[3] - board_pos[1]

    square_mar_wi = board_width / 8
    square_mar_he = board_height / 8

    if who == "b":
        x_square1 = 9 - (ord(str(move)[0]) - 96)
        y_square1 = int(str(move)[1])
        x_square2 = 9 - (ord(str(move)[2]) - 96)
        y_square2 = int(str(move)[3])
    else:
        x_square1 = ord(str(move)[0]) - 96
        y_square1 = 9 - int(str(move)[1])
        x_square2 = ord(str(move)[2]) - 96
        y_square2 = 9 - int(str(move)[3])


    if legit == "y":
        time.sleep(random.randint(1,35)/10)
        hc = HumanClicker()
        curve = HumanCurve(pyautogui.position(), (round(board_pos[0] + (square_mar_wi * x_square1) - square_mar_wi / 2)-random.randint(-13,13),
                    round(board_pos[1] + (square_mar_he * y_square1) - square_mar_he / 2)-random.randint(-13,13)), distortionFrequency=0, tweening=pytweening.easeInOutQuad,
                           offsetBoundaryY=8, offsetBoundaryX=8, targetPoints=random.randint(30,40))
        hc.move((round(board_pos[0] + (square_mar_wi * x_square1) - square_mar_wi / 2),
                    round(board_pos[1] + (square_mar_he * y_square1) - square_mar_he / 2)), duration=0.1, humanCurve=curve)
        pyautogui.click()
        curve = HumanCurve(pyautogui.position(), (round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2)-random.randint(-5,5),
                 round(board_pos[1] + (square_mar_he * y_square2) - square_mar_he / 2)-random.randint(-10,10)),
                           distortionFrequency=0, tweening=pytweening.easeInOutQuad,
                           offsetBoundaryY=8, offsetBoundaryX=8, targetPoints=random.randint(30,40))
        hc.move((round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                 round(board_pos[1] + (square_mar_he * y_square2) - square_mar_he / 2)), duration=0.1, humanCurve = curve)
        pyautogui.click()
    else:
        pyautogui.click(round(board_pos[0] + (square_mar_wi * x_square1) - square_mar_wi / 2),
                    round(board_pos[1] + (square_mar_he * y_square1) - square_mar_he / 2))
        pyautogui.click(round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                    round(board_pos[1] + (square_mar_he * y_square2) - square_mar_he / 2))

    try:
        if str(move)[4] == "q":
            pyautogui.click()
        elif str(move)[4] == "n":
            if legit=="y":
                curve = HumanCurve(pyautogui.position(),
                                   (round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2)-random.randint(-7,7),
                    round(board_pos[1] + (square_mar_he * (y_square2+1)) - square_mar_he / 2)-random.randint(-7,7)),
                                   distortionFrequency=0, tweening=pytweening.easeInOutQuad,
                                   offsetBoundaryY=8, offsetBoundaryX=8, targetPoints=random.randint(30,40))
                hc.move((round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                    round(board_pos[1] + (square_mar_he * (y_square2+1)) - square_mar_he / 2)), duration=0.1,
                        humanCurve=curve)
                pyautogui.click()
            else:
                pyautogui.click(round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                        round(board_pos[1] + (square_mar_he * (y_square2+1)) - square_mar_he / 2))
        elif str(move)[4] == "r":
            if legit == "y":
                curve = HumanCurve(pyautogui.position(),
                                   (round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2)-random.randint(-7,7),
                                    round(board_pos[1] + (square_mar_he * (y_square2 + 2)) - square_mar_he / 2)-random.randint(-7,7)),
                                   distortionFrequency=0, tweening=pytweening.easeInOutQuad,
                                   offsetBoundaryY=8, offsetBoundaryX=8, targetPoints=random.randint(30,40))
                hc.move((round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                         round(board_pos[1] + (square_mar_he * (y_square2 + 2)) - square_mar_he / 2)), duration=0.1,
                        humanCurve=curve)
                pyautogui.click()
            else:
                pyautogui.click(round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                                round(board_pos[1] + (square_mar_he * (y_square2 + 2)) - square_mar_he / 2))
        elif str(move)[4] == "b":
            if legit == "y":
                curve = HumanCurve(pyautogui.position(),
                                   (round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2)-random.randint(-7,7),
                                    round(board_pos[1] + (square_mar_he * (y_square2 + 3)) - square_mar_he / 2)-random.randint(-7,7)),
                                   distortionFrequency=0, tweening=pytweening.easeInOutQuad,
                                   offsetBoundaryY=8, offsetBoundaryX=8, targetPoints=random.randint(30,40))
                hc.move((round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                         round(board_pos[1] + (square_mar_he * (y_square2 + 3)) - square_mar_he / 2)), duration=0.1,
                        humanCurve=curve)
                pyautogui.click()
            else:
                pyautogui.click(round(board_pos[0] + (square_mar_wi * x_square2) - square_mar_wi / 2),
                                round(board_pos[1] + (square_mar_he * (y_square2 + 3)) - square_mar_he / 2))
    except:
        pass


    if board.is_game_over():
        print("Looks like I won again!")
        break
