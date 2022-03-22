# Sweeper

This is a basic ncurses minesweeper game.
It is written in Python, using the awesome [curtsies](https://github.com/bpython/curtsies) library for interacting with the terminal.

## Installation

This requires [poetry](https://python-poetry.org/) to install.
If you don't have `poetry`:

```bash
$ pip install poetry
```

To install the game:

```bash
$ poetry install
```

## Running

Run with `poetry` like so:

```bash
$ poetry run ./sweeper.py
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
