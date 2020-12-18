#!/usr/bin/env python

import time
from typing import List, Optional

from curtsies import FullscreenWindow, Input, fsarray, FSArray, fmtstr, FmtStr
from curtsies import fmtfuncs as ff
import curtsies.events

# source for box chars:
# http://shapecatcher.com/unicode/block/Box_Drawing

class Field:
  """represents the mine field we're solving"""
  pass

class Tick(curtsies.events.ScheduledEvent):
  """An event that represents a tick of game time"""
  pass

class Game:
  """represents the game board, where game state is displayed"""
  SIZE = (10,10)

  def __init__(self, window: FullscreenWindow):
    # save game window, plus window size info
    self.window = window
    self.max_rows = window.height
    self.max_cols = window.width

    # initialize reactor system + schedule first tick
    self.reactor = Input()
    self.schedule_tick = self.reactor.scheduled_event_trigger(Tick)
    self.schedule_tick(when=time.time())

    # initialize game state
    self.field: Optional[Field] = None
    self.menu: Optional[str] = None

    # initialize game display + add borders and header
    self.chars = FSArray(self.max_rows, self.max_cols)
    self.draw_game_border()
    self.draw_header()

  def draw_game_border(self) -> None:
    """Draws a border around the whole board"""
    self.chars[0, 0] = '┌'
    self.chars[0, self.max_cols-1] = '┐'
    self.chars[self.max_rows-1, 0] = '└'
    self.chars[self.max_rows-1, self.max_cols-1] = '┘'

    for row in range(1, self.max_rows - 1):
      self.chars[row, 0] = '│'
      self.chars[row, self.max_cols-1] = '│'

    self.chars[2, 0] = '├'
    self.chars[2, self.max_cols-1] = "┤"

    for col in range(1, self.max_cols - 1):
      self.chars[0, col] = '─'
      self.chars[2, col] = '-'
      self.chars[self.max_rows - 1, col] = '─'

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

  def draw_menu(self, title: FmtStr, items: List[FmtStr]) -> None:
    """Draws the menu of the specified items"""
    height = len(items)
    width = max((
      title.width,
      max(item.width for item in items) if items else 0,
    ))

    header = [
      "╭" + "-" * (width + 2) + "╮",
      "|" + title.center(width + 2) + "|",
      "|" + "-" * (width + 2) + "|",
    ]

    footer = [
      "╰" + "-" * (width + 2) + "╯",
    ]

    body = fsarray(header + ["| " + i.ljust(width) + " |" for i in items] + footer)
    rows = len(body)
    cols = max(row.width for row in body)

    min_row = int(self.max_rows/2 - rows/2)
    min_col = int(self.max_cols/2 - cols/2)
    self.chars[min_row:min_row+rows, min_col:min_col+cols] = body

  def draw_help(self) -> None:
    """brings up the help menu"""
    self.state = "menu"
    items = [
      ('q', 'Quit Sweeper'),
      ('c', 'Close menu'),
      ('←,↑,→,↓', 'Move Cursor'),
      ('d', 'Detonate'),
      ('f', 'Flag as mine'),
      ('SPACE', 'Detonate unflagged'),
    ]

    max_key = max(len(item[0]) for item in items)
    lines = [
      ff.yellow(item[0]).ljust(max_key) + " : " + ff.gray(item[1])
      for item in items
    ]

    self.draw_menu(ff.bold("Help"), lines)

  def clear_main(self) -> None:
    """Hides the game display"""
    height = self.max_rows - 1 - 3 - 1  # subtract 3 rows for header, 1 for footer
    width = self.max_cols - 1 - 1 - 1   # subtract left + right border

    fill = [" " * width] * height
    self.chars[4:4+height, 1:1+width] = fill

  def draw_debug(self) -> None:
    """Draws some debug info about game state"""
    menu = f"menu: {str(self.menu)}"
    self.chars[self.max_rows-2, 1:1+len(menu)] = [menu]

  def update(self) -> None:
    """Updates display based on game state"""
    if self.menu:
      self.clear_main()
      if self.menu == "help":
        self.draw_help()
      else:
        self.draw_menu(ff.blue("test"), [])

    elif self.field:
      self.draw_game_clock()
      self.draw_field()

    else:
      self.clear_main()

    self.draw_debug()
    self.window.render_to_terminal(self.chars)

  def process_event(self, event: Optional[str]) -> None:
    """process an input event"""
    if self.menu and event == "c":
      self.menu = None

    if event == "h":
      self.menu = "help"
    elif event == "t":
      self.menu = "test"

  def play(self) -> None:
    """Main loop of the game"""

    with self.reactor:
      for e in self.reactor:
        self.update()

        if e == '<ESC>' or e == 'q':
          break
        elif isinstance(e, Tick):
          self.schedule_tick(time.time() + 1/15)
        else:
          self.process_event(str(e))

def main() -> None:
  with FullscreenWindow() as window:
    game = Game(window)
    game.play()



if __name__ == "__main__":
  main()
