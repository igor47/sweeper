#!/usr/bin/env python

from dataclasses import dataclass
import pendulum
import random
import time
from typing import List, Dict, Optional, Tuple, Set, Union

from curtsies import FullscreenWindow, Input, fsarray, FSArray, fmtstr, FmtStr
from curtsies import fmtfuncs as ff
import curtsies.events

# source for box chars:
# http://shapecatcher.com/unicode/block/Box_Drawing

class Field:
  """represents the mine field we're solving"""
  CHAR_MAP: Dict[str, str] = {
    'm': '💣',
    'f': '🏳 ',
    'c': '□ '
  }

  def __init__(self):
    self.width = 10
    self.height = 10
    self.mine_count = 10

    # game clock tracking
    self.started: Optional[pendulum.DateTime] = None
    self.ended: Optional[pendulum.DateTime] = None
    self.stoppage_time: pendulum.Duration = pendulum.duration()

    # initialize cursor position
    self.chars: FSArray = fsarray([])
    self.row, self.col = 5, 5
    self.mines: Set[Tuple[int, int]] = self.init_mines()
    self.flagged: Set[Tuple[int, int]] = set()
    self.opened: Set[Tuple[int, int]] = set()
    self.highlighted: Set[Tuple[int, int]] = set()
    self.render()

  @property
  def game_time(self) -> pendulum.Duration:
    """duration that the Field has been worked"""
    if self.started:
      end = self.ended if self.ended else pendulum.now()
      return end - self.started - self.stoppage_time
    else:
      return pendulum.duration()

  @property
  def clock(self) -> FmtStr:
    """game clock as a formatted string"""
    clock = f"{self.game_time.minutes:02d}:{(self.game_time.seconds % 60):02d}"
    if self.game_time.hours > 0:
      clock = f"{self.game_time.hours:02d}:{clock}"

    return ff.plain(clock)

  def add_stoppage(self, stoppage: pendulum.Duration) -> None:
    if self.started and not self.ended:
      self.stoppage_time += stoppage

  def init_mines(self) -> Set[Tuple[int, int]]:
    """Add mines to spaces"""
    mines: Set[Tuple[int, int]] = set()
    while len(mines) < self.mine_count:
      mine = (random.randint(0, self.height - 1), random.randint(0, self.width - 1))
      mines.add(mine)

    return mines

  def neighbors(self, pos: Tuple[int, int]) -> Set[Tuple[int, int]]:
    """returns all neighbors of given position"""
    neighbors = set()
    for rdiff in range(-1, 2):
      for cdiff in range(-1, 2):
        neighbor = (pos[0] + rdiff, pos[1] + cdiff)
        if neighbor == pos:
          continue
        if neighbor[0] < 0 or neighbor[0] >= self.height:
          continue
        if neighbor[1] < 0 or neighbor[1] >= self.width:
          continue

        neighbors.add(neighbor)

    return neighbors

  def neighbor_mines(self, pos: Tuple[int, int]) -> int:
    """number of neighbor mines at given position"""
    return len(self.neighbors(pos) & self.mines)

  def symbol_at(self, pos: Tuple[int, int]) -> Union[str, int]:
    """Returns symbol at given position"""
    if pos in self.opened:
      if pos in self.mines:
        return 'm'
      else:
        return self.neighbor_mines(pos)
    elif pos in self.flagged:
      return 'f'
    else:
      return 'c'

  def char_at(self, pos: Tuple[int, int]) -> FmtStr:
    """returns formatted character at position"""
    sym = self.symbol_at(pos)
    char = f"{sym} " if isinstance(sym, int) else self.CHAR_MAP.get(sym)
    if char == "0 ":
      char = ". "

    kwargs = {}
    if pos[0] == self.row and pos[1] == self.col:
      kwargs['bg'] = 'blue'
    if pos in self.highlighted:
      kwargs['fg'] = 'red'

    return fmtstr(char, **kwargs)

  def render(self) -> None:
    """representation of the field state"""
    rows = []
    for row in range(self.height):
      row_str = self.char_at((row, 0))
      for col in range(1, self.width):
        row_str = row_str.append(self.char_at((row, col)))

      rows.append(row_str)

    self.chars = fsarray(rows)
    self.highlighted = set()

  def move(self, row: int, col: int) -> None:
    """move the position"""
    if row == 0 and col == 0:
      return
    if abs(row) + abs(col) > 1:
      raise ValueError("can only move the cursor by one spot")

    self.row = self.row + row if 0 <= self.row + row < self.height else self.row
    self.col = self.col + col if 0 <= self.col + col < self.height else self.col

    self.render()

  def open_at(self, pos: Tuple[int, int]) -> None:
    """actually opens at specified position"""
    self.opened.add(pos)
    if self.symbol_at(pos) == 0:
      neighbors = self.neighbors(pos)
      still_closed = neighbors - self.opened
      for neighbor in still_closed:
        self.open_at(neighbor)

  def clear_at(self, pos: Tuple[int, int]) -> None:
    """on an open square, opens remaining unflagged squares or highlights"""
    count = self.symbol_at(pos)
    neighbors = self.neighbors(pos)

    flagged = neighbors & self.flagged
    unflagged = neighbors - self.flagged

    if len(flagged) == count:
      for neighbor in unflagged:
        self.open_at(neighbor)
    else:
      self.highlighted = unflagged - self.opened

  def open(self) -> None:
    """Opens mine, or adjecent squares, under cursor"""
    if not self.started:
      self.started = pendulum.now()

    pos = (self.row, self.col)
    if pos in self.opened:
      self.clear_at(pos)
    else:
      self.open_at(pos)

    self.render()

  def flag(self) -> None:
    """flag space at cursor"""
    pos = (self.row, self.col)
    if pos in self.flagged:
      self.flagged.remove(pos)
    else:
      self.flagged.add(pos)

    self.render()

  @property
  def lost(self) -> bool:
    """True if we lost"""
    lost = bool(self.mines & self.opened)
    if lost and not self.ended:
      self.ended = pendulum.now()

    return lost

  @property
  def won(self) -> bool:
    """true if we won"""
    won = len(self.opened) + len(self.mines) == self.width * self.height
    if won and not self.ended:
      self.ended = pendulum.now()

    return won

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
    self.last_event: Optional[str] = None

    # initialize game state
    self.field: Optional[Field] = None
    self.menu: Optional[str] = None
    self.menu_opened_at: Optional[pendulum.DateTime] = None

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

    clock = ff.plain('┊ ') + ff.green(self.field.clock if self.field else "00:00")
    self.chars[1, (self.max_cols - 1 - clock.width):(self.max_cols - 1)] = [clock]

    avail = self.max_cols - 2 - title.width - clock.width

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

    self.chars[1, title.width:(title.width + istr.width)] = [istr]

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
      ('n', 'New game'),
      ('←,↑,→,↓', 'Move Cursor'),
      ('f', 'Flag/unflag'),
      ('SPACE', 'Clear'),
    ]

    max_key = max(len(item[0]) for item in items)
    lines = [
      ff.yellow(item[0]).ljust(max_key) + " : " + ff.gray(item[1])
      for item in items
    ]

    self.draw_menu(ff.bold("Help"), lines)

  def draw_confirm_new(self) -> None:
    """Confirms we want to restart the game"""
    items = [
      ff.red("A game is already in-progress!"),
      ff.plain("Press ") + fmtstr("n", fg="yellow", underline=True) + " again to start a new",
      ff.plain("game, or ") + fmtstr("c", fg="yellow", underline=True) + " to cancel",
    ]

    self.draw_menu(ff.plain("Restart?"), items)

  def draw_won(self) -> None:
    """Confirms we want to restart the game"""
    assert self.field is not None

    items = [
      ff.plain(f"Congratulations! You won in {self.field.game_time.in_words()}"),
      ff.plain(f"Press ") + fmtstr("n", fg="yellow", underline=True) + " to start a new game,",
      ff.plain("or ") + fmtstr("c", fg="yellow", underline=True) + " to savor your success.",

    ]

    self.draw_menu(ff.green("Victory!"), items)

  def draw_lost(self) -> None:
    """Confirms we want to restart the game"""
    assert self.field is not None

    items = [
      ff.plain(f"Alas, you appear to have ") + fmtstr("exploded", fg="red", bold=True) + ".",
      ff.plain(f"Press ") + fmtstr("n", fg="yellow", underline=True) + " to start a new game,",
      ff.plain("or ") + fmtstr("c", fg="yellow", underline=True) + " to learn from failure.",
    ]

    self.draw_menu(ff.red("Defeat!"), items)

  def draw_field(self) -> None:
    """draws the minefield on the board"""
    if not self.field:
      return

    field = self.field.chars
    rows, cols = field.shape

    min_row = int(self.max_rows/2 - rows/2)
    min_col = int(self.max_cols/2 - cols/2)
    self.chars[min_row:min_row+rows, min_col:min_col+cols] = field

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

    event = f"event: {str(self.last_event)}"
    self.chars[self.max_rows-3, 1:1+len(event)] = [event]

  def update(self) -> None:
    """Updates display based on game state"""
    self.clear_main()

    if self.menu:
      if not self.menu_opened_at:
        self.menu_opened_at = pendulum.now()

      self.clear_main()
      if self.menu == "help":
        self.draw_help()
      elif self.menu == "confirm_new":
        self.draw_confirm_new()
      elif self.menu == "won":
        self.draw_won()
      elif self.menu == "lost":
        self.draw_lost()
      else:
        self.draw_menu(ff.blue("test"), [])

    elif self.field:
      if self.menu_opened_at:
        self.field.add_stoppage(pendulum.now() - self.menu_opened_at)
        self.menu_opened_at = None

      self.draw_header()
      self.draw_field()
      if not self.field.ended:
        if self.field.won:
          self.menu = "won"
        elif self.field.lost:
          self.menu = "lost"

    self.draw_debug()
    self.window.render_to_terminal(self.chars)

  def process_event(self, event: Optional[str]) -> None:
    """process an input event"""
    self.last_event = event

    if self.menu and event == "c":
      self.menu = None

    if event == "h":
      self.menu = "help"

    if event == "t":
      self.menu = "test"

    if event == "n":
      if not self.field or self.field.ended or self.menu == "confirm_new":
        self.menu = None
        self.field = Field()
      else:
        self.menu = "confirm_new"

    if self.field:
      if event == "<SPACE>":
        self.field.open()
      if event == "<UP>":
        self.field.move(-1, 0)
      if event == "<LEFT>":
        self.field.move(0, -1)
      if event == "<RIGHT>":
        self.field.move(0, 1)
      if event == "<DOWN>":
        self.field.move(1, 0)
      if event == "f":
        self.field.flag()

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
