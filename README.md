# Sweeper

This is a basic ncurses minesweeper game.
It is written in Python, using the awesome [curtsies](https://github.com/bpython/curtsies) library for interacting with the terminal.

## Running

This is a single-file script that uses [PEP 723](https://peps.python.org/pep-0723/) inline metadata, so [`uv`](https://docs.astral.sh/uv/) handles everything — Python version, virtualenv, and dependencies — on first run.

```bash
$ ./sweeper.py
```

Or, equivalently:

```bash
$ uv run sweeper.py
```

## Interface

The following commands are supported:

------------------------------------
| Key | Action                      |
| :-: | :--                         |
| h   | Display in-game help menu   |
| c   | Close any open in-game menu |
| l   | Pick difficulty level       |
| n   | Start a new game            |
------------------------------------

While a game is in-progress, use the arrow keys (←,↑,→,↓) to move the cursor around the mine field.
Hit `<SPACE>` to open the cell under the cursor.
Hit `f` to flag a cell as a mine.
Hitting `<SPACE>` on an already-opened clue cell will highlight adjacent cells.
If the number of neighboring cells that are flagged equals the value of the clue, then all remaining unflagged cells will be opened.

## Screenshot

<img src="https://raw.github.com/igor47/sweeper/master/sweeper.png" />

## TODO

I wanted to implement a version of sweeper where you don't have to guess, but this turned out to be more complicated than I thought.
