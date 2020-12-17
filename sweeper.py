#!/usr/bin/env python

import time
from typing import List

from curtsies import FullscreenWindow, Input, FSArray, fmtstr, FmtStr
from curtsies import fmtfuncs as ff

class Game:
  STATE = 'new'
  SIZE = (10,10)

  def __init__(self, max_rows: int, max_cols: int):
    self.max_rows = max_rows
    self.max_cols = max_cols

    self.chars = FSArray(self.max_rows, self.max_cols)

    # initializing the game board
    self.draw_game_border()
    self.draw_header()

  def draw_game_border(self) -> None:
    """Draws a border around the whole board"""
    self.chars[0, 0] = '⌜'
    self.chars[0, self.max_cols-1] = '⌝'
    self.chars[self.max_rows-1, 0] = '⌞'
    self.chars[self.max_rows-1, self.max_cols-1] = '⌟'

    for row in range(1, self.max_rows - 1):
      self.chars[row, 0] = '|'
      self.chars[row, self.max_cols-1] = '|'

    for col in range(1, self.max_cols - 1):
      self.chars[0, col] = '¯'
      self.chars[2, col] = '-'
      self.chars[self.max_rows - 1, col] = '_'

  def draw_header(self) -> None:
    """renders the header into our array"""
    title = fmtstr(" No-Guess Sweeper :", fg="blue", underline=True)
    self.chars[1, 1:1+title.width] = [title]
    avail = self.max_cols - 2 - title.width

    instructions: List[FmtStr] = [
      ff.yellow(' h: ') + ff.gray("Help "),
      ff.yellow(' q: ') + ff.gray("Quit "),
      ff.yellow(' n: ') + ff.gray("New "),
    ]

    # drop instructions until they fit on top line
    while sum(i.width for i in instructions) > avail:
      instructions.pop()

    per = int(avail / len(instructions))
    istr = FmtStr().join(i.ljust(per) for i in instructions)

    self.chars[1, (self.max_cols - istr.width - 1):self.max_cols-1] = [istr]

def main() -> None:
  print("main")
  with FullscreenWindow() as window:
    game = Game(window.height, window.width)
    window.render_to_terminal(game.chars)

    with Input() as input_generator:
      for c in input_generator:
        if c == '<ESC>' or c == 'q':
          break


if __name__ == "__main__":
  main()
