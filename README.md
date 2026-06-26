# Auto-Chess

A chess bot that watches your screen, automatically detects the board, calculates the best move with a chess engine, and plays it for you by controlling the mouse — completely hands-free.

It works by taking screenshots, recognizing the position with a TensorFlow neural network, feeding it to a UCI chess engine (such as Stockfish), and then moving and clicking the pieces for you. It also listens for the opponent's moves and responds automatically, so once it's running you don't have to touch anything.

> ⚠️ **Disclaimer:** This project is for **educational purposes only**. See the [Disclaimer](#disclaimer) section below.

## Features

- **Fully automatic play** — detects the position, picks the best move, and plays it without any input from you.
- **Opponent move detection** — continuously watches the board and reacts as soon as the opponent moves.
- **Engine-powered** — uses any UCI-compatible engine (Stockfish 13 recommended) with adjustable thinking time.
- **Neural-network board recognition** — reads the board straight from the screen using a TensorFlow model, so no integration with the chess site is required.
- **Plays as white or black** — just tell it which side you are.
- **Auto-promotion handling** — automatically handles queen, knight, rook, and bishop promotions.
- **Legit mode** — moves the mouse in a human-like way (curved paths, randomized timing, off-center clicks) to make the automation less obvious.

## How it works

1. Grabs a screenshot of your screen.
2. Locates the chessboard and recognizes the position using the bundled TensorFlow chessbot model.
3. Detects the opponent's last move by comparing positions.
4. Asks the chess engine for the best move.
5. Calculates the on-screen coordinates of the move and clicks the squares to play it.
6. Repeats — waiting for the opponent and then responding automatically.

## Requirements

- Python 3
- A UCI chess engine — [Stockfish 13](https://stockfishchess.org/download/) is recommended.
- The Python libraries listed in `requirements.txt`.

## Installation

1. Install the required libraries:

   ```bash
   pip install -r requirements.txt
   ```

   > **Note:** `pyclick` is only needed if you plan to use legit mode.

2. Download a chess engine. [Stockfish 13](https://stockfishchess.org/download/) is recommended.

3. Open `Auto-Chess.py` and set `engine_path` to the absolute path of your engine executable:

   ```python
   engine_path = r"Engine Path"  # <-- replace with the path to your engine
   ```

## Usage

1. Open a chess game so the board is **fully visible** on your screen.
2. Run the script:

   ```bash
   python Auto-Chess.py
   ```

3. Answer the prompts:
   - Whether you want **legit mode** (`y`/`n`).
   - Whether you are playing as **white** or **black**.

That's it — the bot will start playing for you and automatically respond to the opponent's moves.

### Settings

You can tweak the behavior at the top of `Auto-Chess.py`:

- `wait_interval` — the wait time between screenshots / retries.
- `engine_path` — the absolute path to your engine executable.
- `engine_think_time` — how long the engine thinks per move. Higher values play stronger but slower.

### Legit mode

Legit mode is designed to make the automation harder to detect. Instead of instantly clicking the center of each square, it:

- Moves the mouse along human-like, curved paths at randomized speeds.
- Clicks slightly off-center rather than dead center on each piece.
- Waits random intervals before playing.

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
