# Auto-Chess

A chess bot that watches your screen, automatically detects the board, decides on a move, and plays it for you by controlling the mouse — completely hands-free.

It works by taking screenshots, recognizing the position with a TensorFlow neural network, choosing a move with either a human-like neural network (**Maia**) or a classical engine (**Stockfish**), and then moving and clicking the pieces for you. It also listens for the opponent's moves and responds automatically, so once it's running you don't have to touch anything.

> ⚠️ **Disclaimer:** This project is for **educational purposes only**. See the [Disclaimer](#disclaimer) section below.

## Features

- **Fully automatic play** — detects the position, decides on a move, and plays it without any input from you.
- **Opponent move detection** — continuously watches the board and reacts as soon as the opponent moves.
- **Human-like ML move selection (Maia)** — plays the move a real human of a chosen rating would likely make, using the [Maia](https://github.com/CSSLab/maia-chess) neural network instead of always finding the engine-perfect move.
- **Maia + Stockfish blunder veto** — Maia chooses the move, but Stockfish double-checks it and steps in only when Maia is about to make a real blunder, so play stays human-like without throwing the game.
- **Stockfish engine mode** — prefer raw strength? Use any UCI-compatible engine (Stockfish 13+ recommended) with adjustable thinking time and an optional Elo cap.
- **Neural-network board recognition** — reads the board straight from the screen using a TensorFlow model, so no integration with the chess site is required.
- **Plays as white or black** — just tell it which side you are.
- **Auto-promotion handling** — automatically handles queen, knight, rook, and bishop promotions.
- **Legit mode** — moves the mouse in a human-like way (curved paths, randomized timing, off-center clicks) to make the automation less obvious.

## How it works

1. Grabs a screenshot of your screen.
2. Locates the chessboard and recognizes the position using the bundled TensorFlow chessbot model.
3. Detects the opponent's last move by comparing positions.
4. Decides on a move:
   - **Maia + Stockfish** (default) — Maia predicts a human-like move, and Stockfish overrides it only if it loses too much (a blunder).
   - **Maia only** — plays Maia's human-like move as-is.
   - **Stockfish only** — plays the engine's best move (optionally Elo-capped).
5. Calculates the on-screen coordinates of the move and clicks the squares to play it.
6. Repeats — waiting for the opponent and then responding automatically.

## Requirements

- Python 3
- **Stockfish** — [Stockfish 13+](https://stockfishchess.org/download/) (used as the engine and as the blunder-checker for Maia).
- **lc0 + Maia weights** (for the human-like modes) — the [lc0](https://github.com/LeelaChessZero/lc0/releases) executable plus one or more [Maia weight files](https://github.com/CSSLab/maia-chess/tree/master/maia_weights) (`maia-1100.pb.gz` … `maia-1900.pb.gz`).
- The Python libraries listed in `requirements.txt`.

## Installation

1. Install the required libraries:

   ```bash
   pip install -r requirements.txt
   ```

   > **Note:** `pyclick` is only needed if you plan to use legit mode.

2. Download **Stockfish** ([Stockfish 13+](https://stockfishchess.org/download/)).

3. For the human-like Maia modes, download **lc0** ([releases](https://github.com/LeelaChessZero/lc0/releases)) and the **Maia weights** you want ([`maia-1100.pb.gz` … `maia-1900.pb.gz`](https://github.com/CSSLab/maia-chess/tree/master/maia_weights)). Put all the weight files in one folder.

   > **Note:** GitHub sometimes unzips downloads automatically. Maia/lc0 expects the **gzipped** files, so make sure the filenames stay `maia-XXXX.pb.gz`. If you only want Stockfish-only mode, you can skip lc0 and Maia entirely.

4. Open `Auto-Chess.py` and set the paths near the top:

   ```python
   stockfish_path   = r"Stockfish Path"     # absolute path to the Stockfish executable
   lc0_path         = r"Lc0 Path"           # absolute path to the lc0 executable (Maia modes)
   maia_weights_dir = r"Maia Weights Dir"   # folder containing the maia-XXXX.pb.gz files
   ```

## Usage

1. Open a chess game so the board is **fully visible** on your screen.
2. Run the script:

   ```bash
   python Auto-Chess.py
   ```

3. Answer the prompts:
   - Whether you want **legit mode** (`y`/`n`).
   - The **engine mode** — `1` Maia + Stockfish, `2` Maia only, or `3` Stockfish only.
   - For the Maia modes: the **Maia rating** (`1100`–`1900`, blank for `1500`).
   - For Stockfish-only mode: the **Elo** to play at (leave blank for full strength).
   - Whether you are playing as **white** or **black**.

That's it — the bot will start playing for you and automatically respond to the opponent's moves.

### Settings

You can tweak the behavior at the top of `Auto-Chess.py`:

- `wait_interval` — the wait time between screenshots / retries.
- `stockfish_path` — absolute path to the Stockfish executable.
- `lc0_path` / `maia_weights_dir` — absolute path to lc0 and the folder of Maia weights (Maia modes).
- `engine_think_time` — how long Stockfish thinks per move / per blunder check. Higher = stronger but slower.
- `maia_rating` — default Maia model to use (`1100`–`1900`). The startup prompt overrides this.
- `blunder_threshold` — in *Maia + Stockfish* mode, how many centipawns Maia's move may lose before Stockfish overrides it. Lower = stricter (closer to Stockfish), higher = more human (more of Maia's moves get through). Default `150`.
- `engine_elo` — default Elo cap for Stockfish-only mode (`None` = full strength). The startup prompt overrides this.

### Engine modes

The biggest giveaway that you're using a bot is playing the engine-perfect move every single time. To make play look human, the bot can choose moves with **Maia** — a neural network trained on millions of real human games that predicts the move a human of a given rating would actually play (including human-style mistakes).

There are three modes, chosen on startup:

- **Maia + Stockfish (recommended).** Maia picks a human-like move; Stockfish evaluates it and only overrides it when it's a genuine blunder (loses more than `blunder_threshold` centipawns). You get human-looking play without throwing games to obvious one-move blunders.
- **Maia only.** Plays Maia's move as-is — the most human, but it will occasionally make the same mistakes a player of that rating would.
- **Stockfish only.** Classic full-strength engine play, with an optional **Elo cap** (uses Stockfish's `UCI_LimitStrength` / `UCI_Elo`; the bot shows the supported range and clamps your input, falling back to full strength with a warning if the engine doesn't support it).

Maia runs inside **lc0** with search disabled (a single policy evaluation, `go nodes 1`), so it's fast — it just asks the network "what would a human play here?" once per move. See [CSSLab/maia-chess](https://github.com/CSSLab/maia-chess) for details and the model files.

### Legit mode

Legit mode is designed to make the automation harder to detect. Instead of instantly clicking the center of each square, it:

- Moves the mouse along human-like, curved paths at randomized speeds.
- Clicks slightly off-center rather than dead center on each piece.
- Waits random intervals before playing.

Pair it with a **Maia** engine mode so the *moves* look human too, not just the mouse — human move choice + human-like mouse movement is far more convincing than either alone.

The bot has been tested on **chess.com** and **lichess.org**, but should work on pretty much any chess site with a few tweaks.

## Troubleshooting

**The bot isn't detecting the board:**
- On chess.com, set the board scheme to **brown** and the pieces to **classical** in settings.
- Try making the board size *slightly* smaller — this often improves detection. The ideal size depends on your screen resolution, so experiment to find what works best.

**The bot detects the wrong position or says the position is invalid:**
- **Disable piece animations** — screenshots taken mid-animation can place pieces on the wrong squares.
- **Disable "highlight last move"** — this has been known to throw off detection.

> The model was trained on lichess, so play there for optimal results. It still works fine on chess.com and other sites with a few tweaks.

## Showcase

A short demo video is available on Google Drive: [watch here](https://drive.google.com/file/d/1XvPG42slB2txM0sW6VHnB4g4HXXF496n/view?usp=sharing).

> The video is fairly outdated and the bot has been improved a lot since — please try it out yourself!

## Disclaimer

This project is meant **only for educational purposes**, and I will not be responsible for what happens if you use it to cheat.

This was not built as a cheating tool — you can already cheat at online chess freely without it. I made it to learn how machine learning works and how to implement it, and because I've always enjoyed automation projects like this one.

## Credits

The chessboard detection is **not** my own work — it comes from Elucidation's [tensorflow_chessbot](https://github.com/Elucidation/tensorflow_chessbot), which I modified to better suit this project's needs.

The human-like move selection uses [Maia Chess](https://github.com/CSSLab/maia-chess) (CSSLab), a neural network engine trained on human games, run via [Leela Chess Zero (lc0)](https://github.com/LeelaChessZero/lc0). Best-move and blunder-checking are powered by [Stockfish](https://stockfishchess.org/).
