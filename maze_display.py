"""Visual representation for A-Maze-ing project."""


import sys
import random
from mazegen import MazeGenerator

from mazegen.generator import NORTH, EAST, SOUTH, WEST
from maze_writer import write_maze

RESET = "\033[0m"
WALL_COLOURS = {
    "1": ("white",   "\033[97m"),
    "2": ("green",   "\033[92m"),
    "3": ("yellow",  "\033[93m"),
    "4": ("blue",    "\033[94m"),
    "5": ("magenta", "\033[95m"),
    "6": ("cyan",    "\033[96m"),
    "7": ("red",     "\033[91m"),
}

PATH = "\033[96m"
ENTRY = "\033[92m"
EXIT = "\033[91m"
PAT_BG = "\033[43m\033[30m"


class MazeVisual:
    """Terminal renderer for the maze.

    Attributes:
        gen:       The MazeGenerator instance.
        show_path: Toggle solution path overlay.
        wall_col:  Current ANSI wall colour string.
        wall_name: Human-readable wall colour name.
    """

    def __init__(self, gen: MazeGenerator, output_file: str) -> None:
        self.gen = gen
        self.output_file = output_file
        self.show_path = False
        self.wall_col = "\033[97m"
        self.wall_name = "white"

    def run(self) -> None:
        """Start the interactive loop."""
        while True:
            self._clear()
            self._draw()
            self._menu()
            choice = input("Choice (1-4): ").strip()
            if choice == "1":
                self._regenerate()
            elif choice == "2":
                self.show_path = not self.show_path
            elif choice == "3":
                self._pick_colour()
            elif choice == "4":
                print("Goodbye!")
                sys.exit(0)

    def _draw(self) -> None:
        """Render the full maze grid to the terminal."""
        for row in range(self.gen.height):
            print(self._top_row(row))
            print(self._mid_row(row))
        print(self._bottom_row())

    def _top_row(self, row: int) -> str:
        """Build the top-border line for a given row.

        Each cell contributes: corner (+) + north wall (--- or spaces).
        Pattern cells get a yellow background on their wall segments.
        """
        line = ""
        for col in range(self.gen.width):
            is_pat = (col, row) in self.gen._pattern_cells
            line += self._corner(col, row)
            line += self._hwall(col, row, NORTH, is_pat)
        line += self._corner(self.gen.width, row)
        return line

    def _mid_row(self, row: int) -> str:
        """Build the middle line for a given row.

        Each cell contributes: west wall (|) + 3-char cell body.
        The last cell also appends its east wall.
        """
        line = ""
        for col in range(self.gen.width):
            is_pat = (col, row) in self.gen._pattern_cells
            line += self._vwall(col, row, WEST, is_pat)
            line += self._body(col, row)
        last = self.gen.width - 1
        is_last_pat = (last, row) in self.gen._pattern_cells
        line += self._vwall(last, row, EAST, is_last_pat)
        return line

    def _bottom_row(self) -> str:
        """Build the bottom-border line (south walls of the last row)."""
        row = self.gen.height - 1
        line = ""
        for col in range(self.gen.width):
            is_pat = (col, row) in self.gen._pattern_cells
            line += self._corner(col, row + 1)
            line += self._hwall(col, row, SOUTH, is_pat)
        line += self._corner(self.gen.width, row + 1)
        return line


    def _corner(self, col: int, row: int) -> str:
        """Return a '+' corner, yellow only when surrounded by pattern cells.

        The corner sits at the intersection of 4 cells:
          top-left=(col-1,row-1)  top-right=(col,row-1)
          bot-left=(col-1,row)    bot-right=(col,row)

        We only colour it yellow when ALL four touching cells that actually
        exist inside the grid are pattern cells — this keeps the yellow
        strictly inside the "42" blocks and prevents it bleeding into
        neighbouring corridors.
        """
        pat = self.gen._pattern_cells
        touching = [
            (col - 1, row - 1), (col, row - 1),
            (col - 1, row),     (col, row),
        ]
        inside = [
            (x, y) for (x, y) in touching
            if 0 <= x < self.gen.width and 0 <= y < self.gen.height
        ]
        is_pat = inside and all(p in pat for p in inside)
        prefix = PAT_BG if is_pat else ""
        return prefix + self.wall_col + "+" + RESET

    def _hwall(self, col: int, row: int, direction: int, is_pat: bool) -> str:
        """Return a 3-char horizontal wall segment (--- or spaces).

        Yellow background only when BOTH this cell and the cell on the
        other side of the wall are pattern cells — keeps yellow strictly
        inside the "42" shape.

        Args:
            col:       Column of the cell.
            row:       Row of the cell.
            direction: NORTH or SOUTH bit to check.
            is_pat:    Whether this cell is a pattern cell.
        """
        has_wall = bool(self.gen.grid[row][col] & direction)
        ny = row - 1 if direction == NORTH else row + 1
        other_pat = (col, ny) in self.gen._pattern_cells
        both_pat = is_pat and other_pat
        if has_wall:
            prefix = PAT_BG if both_pat else ""
            return prefix + self.wall_col + "---" + RESET
        else:
            return (PAT_BG + "   " + RESET) if is_pat else "   "

    def _vwall(self, col: int, row: int, direction: int, is_pat: bool) -> str:
        """Return a 1-char vertical wall segment (| or space).

        Yellow background only when BOTH this cell and the cell on the
        other side of the wall are pattern cells.

        For WEST walls: col is the current cell being drawn.
        For EAST walls: col is the last cell (width-1), direction=EAST.

        Args:
            col:       Column of the cell whose wall to check.
            row:       Row of the cell.
            direction: WEST or EAST bit to check.
            is_pat:    Whether this cell is a pattern cell.
        """
        has_wall = bool(self.gen.grid[row][col] & direction)
        nx = col - 1 if direction == WEST else col + 1
        other_pat = (nx, row) in self.gen._pattern_cells
        both_pat = is_pat and other_pat
        if has_wall:
            prefix = PAT_BG if both_pat else ""
            return prefix + self.wall_col + "|" + RESET
        else:
            return (PAT_BG + " " + RESET) if is_pat else " "

    def _body(self, col: int, row: int) -> str:
        """Return the 3-char content of a cell.

        Priority: entry > exit > pattern > path dot > empty.
        """
        pos = (col, row)
        if pos == self.gen.entry:
            return ENTRY + "███" + RESET
        if pos == self.gen.exit_:
            return EXIT + "███" + RESET
        if pos in self.gen._pattern_cells:
            return PAT_BG + "###" + RESET
        if self.show_path and pos in self._path_cells():
            return PATH + " * " + RESET
        return "   "


    def _regenerate(self) -> None:
        """Reset state, generate a new maze, and update the output file."""
        self.gen.seed = random.randint(0, 99999)
        self.gen.grid = []
        self.gen.solution = ""
        self.gen._visited = []
        self.gen._pattern_cells = set()
        self.gen.generate()
        write_maze(self.gen, self.output_file)
        self.show_path = False

    def _pick_colour(self) -> None:
        """Let the user choose a new wall colour."""
        self._clear()
        print("Choose a wall colour:\n")
        for key, (name, code) in WALL_COLOURS.items():
            print(f"  {key}. {code}{name}{RESET}")
        print()
        choice = input("Pick (1-7): ").strip()
        if choice in WALL_COLOURS:
            self.wall_name, self.wall_col = WALL_COLOURS[choice]


    def _path_cells(self) -> set[tuple[int, int]]:
        """Convert solution string to a set of (x, y) cells on the path."""
        cells: set[tuple[int, int]] = set()
        if not self.gen.solution:
            return cells
        x, y = self.gen.entry
        deltas = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
        cells.add((x, y))
        for letter in self.gen.solution:
            dx, dy = deltas[letter]
            x += dx
            y += dy
            cells.add((x, y))
        return cells

    def _clear(self) -> None:
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="")

    def _menu(self) -> None:
        """Print the menu."""
        toggle = "Hide" if self.show_path else "Show"
        print("\n=== A-Maze-ing ===")
        print("1. Re-generate maze")
        print(f"2. {toggle} shortest path")
        print(f"3. Change wall colour  "
              f"(current: {self.wall_col}{self.wall_name}{RESET})")
        print("4. Quit\n")
