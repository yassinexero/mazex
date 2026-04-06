"""Maze generation module for A-Maze-ing project.

This module provides the MazeGenerator class which implements maze generation
using the Recursive Backtracker (DFS) algorithm.

Wall encoding (per cell, 4-bit integer):
    Bit 0 (LSB) = North wall
    Bit 1       = East wall
    Bit 2       = South wall
    Bit 3       = West wall
    1 = wall closed, 0 = wall open

Example usage:
    from maze_generator import MazeGenerator

    gen = MazeGenerator(width=20, height=15, entry=(0, 0), exit_=(19, 14),
                        perfect=True, seed=42)
    gen.generate()

    grid     = gen.grid      # 2D list of hex wall values
    path     = gen.solution  # "EESSENWW..." direction string
    entry    = gen.entry     # (x, y)
    exit_    = gen.exit_     # (x, y)
"""

import random
from collections import deque

# ── Wall bit masks ────────────────────────────────────────────────────────────
NORTH: int = 0b0001  # bit 0
EAST:  int = 0b0010  # bit 1
SOUTH: int = 0b0100  # bit 2
WEST:  int = 0b1000  # bit 3

ALL_WALLS: int = NORTH | EAST | SOUTH | WEST  # 0xF

# ── Directions ────────────────────────────────────────────────────────────────
# Each tuple: (dx, dy, wall on current cell, wall on neighbor)
DIRECTIONS: list[tuple[int, int, int, int]] = [
    (0, -1, NORTH, SOUTH),
    (1,  0, EAST,  WEST),
    (0,  1, SOUTH, NORTH),
    (-1, 0, WEST,  EAST),
]

# Maps movement vector → direction letter (used in BFS path reconstruction)
DIR_LETTER: dict[tuple[int, int], str] = {
    (0, -1): "N",
    (1,  0): "E",
    (0,  1): "S",
    (-1, 0): "W",
}

# ── "42" pixel pattern ────────────────────────────────────────────────────────
# 7 rows x 9 cols. 1 = solid walled cell, 0 = normal cell DFS can carve.
# Col 4 (all zeros) is the gap between the "4" and the "2".
#
#   4   4  .  2222
#   4   4  .  2  2
#   4   4  .     2
#   44444  .  2222
#       4  .  2
#       4  .  2
#       4  .  2222
#
PATTERN_42: list[list[int]] = [
    [1, 0, 1,  0,  1, 1, 1],
    [1, 0, 1,  0,  0, 0, 1],
    [1, 1, 1,  0,  1, 1, 1],
    [0, 0, 1,  0,  1, 0, 0],
    [0, 0, 1,  0,  1, 1, 1],
]

PATTERN_HEIGHT: int = len(PATTERN_42)      # 5
PATTERN_WIDTH:  int = len(PATTERN_42[0])   # 7

# Minimum maze size to fit the pattern with 2-cell buffer on each side
MIN_MAZE_WIDTH:  int = PATTERN_WIDTH  + 2  # 9
MIN_MAZE_HEIGHT: int = PATTERN_HEIGHT + 2  # 7


def pattern_cells(maze_width: int, maze_height: int) -> set[tuple[int, int]]:
    """Return the set of grid coordinates occupied by the '42' pattern.

    The pattern is centered in the maze using integer division.

    Args:
        maze_width:  Number of columns in the maze.
        maze_height: Number of rows in the maze.

    Returns:
        Set of (x, y) coordinates that belong to the '42' pattern.
    """
    origin_x = (maze_width  - PATTERN_WIDTH)  // 2
    origin_y = (maze_height - PATTERN_HEIGHT) // 2
    cells: set[tuple[int, int]] = set()
    for row_idx, row in enumerate(PATTERN_42):
        for col_idx, cell in enumerate(row):
            if cell == 1:
                cells.add((origin_x + col_idx, origin_y + row_idx))
    return cells


class MazeGenerator:
    """Generates a maze using the Recursive Backtracker (DFS) algorithm.

    The maze is stored as a 2D grid where each cell is a 4-bit integer
    encoding which walls are closed (1) or open (0).

    Attributes:
        width:          Number of columns.
        height:         Number of rows.
        entry:          (x, y) entry cell coordinates.
        exit_:          (x, y) exit cell coordinates.
        perfect:        If True, generates a perfect maze (one unique path).
        seed:           Random seed for reproducibility.
        grid:           2D list of ints representing the maze after generation.
        solution:       String of N/E/S/W directions from entry to exit.
        _visited:       2D bool grid tracking which cells DFS has carved.
        _pattern_cells: Set of (x, y) coords belonging to the "42" pattern.
    """

    def __init__(
        self,
        width:   int,
        height:  int,
        entry:   tuple[int, int],
        exit_:   tuple[int, int],
        perfect: bool = True,
        seed:    int | None = None,
    ) -> None:
        """Initialize the MazeGenerator.

        Args:
            width:   Number of columns in the maze.
            height:  Number of rows in the maze.
            entry:   (x, y) coordinates of the entry cell.
            exit_:   (x, y) coordinates of the exit cell.
            perfect: Whether to generate a perfect maze.
            seed:    Optional random seed for reproducible generation.
        """
        self.width = width
        self.height = height
        self.entry = entry
        self.exit_ = exit_
        self.perfect = perfect
        self.seed = seed

        self.grid: list[list[int]] = []
        self.solution: str = ""
        self._visited: list[list[bool]] = []
        self._pattern_cells: set[tuple[int, int]] = set()

    # ── Public API ─────────────────────────────────────────────────────────

    def generate(self) -> None:
        """Generate the maze.

        Pipeline:
        1. Initialize grid — all walls closed.
        2. Reserve "42" pattern cells so DFS skips them.
        3. Run DFS from entry to carve passages.
        4. If non-perfect mode, add extra passages to create loops.
        5. Fix any 3×3 fully open areas.
        6. Solve with BFS to get the shortest path.
        """
        random.seed(self.seed)
        self._init_grid()
        self._reserve_pattern()
        self._visited[self.entry[1]][self.entry[0]] = True
        self._dfs(self.entry[0], self.entry[1])
        if not self.perfect:
            self._add_extra_passages()
        self._fix_open_areas()
        self.solution = self._bfs_solve()

    # ── Grid initialization ────────────────────────────────────────────────

    def _init_grid(self) -> None:
        """Initialize the grid with all walls closed and visited map False."""
        self.grid = [
            [ALL_WALLS] * self.width for _ in range(self.height)
        ]
        self._visited = [
            [False] * self.width for _ in range(self.height)
        ]

    # ── "42" pattern reservation ───────────────────────────────────────────

    def _reserve_pattern(self) -> None:
        """Reserve "42" pattern cells before DFS runs.

        Marks each pattern cell as visited (so DFS skips it) and keeps
        all its walls closed. Size is guaranteed valid by config_parser.
        """
        self._pattern_cells = pattern_cells(self.width, self.height)
        for gx, gy in self._pattern_cells:
            self._visited[gy][gx] = True
            self.grid[gy][gx] = ALL_WALLS

    # ── DFS ────────────────────────────────────────────────────────────────

    def _dfs(self, start_x: int, start_y: int) -> None:
        """Run iterative DFS from the given start cell to carve passages.

        Uses an explicit stack to avoid Python recursion depth limits
        on large mazes.

        Args:
            start_x: X coordinate of the starting cell.
            start_y: Y coordinate of the starting cell.
        """
        stack: list[tuple[int, int]] = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            dirs = list(DIRECTIONS)
            random.shuffle(dirs)

            moved = False
            for dx, dy, wall_cur, wall_nbr in dirs:
                nx, ny = x + dx, y + dy
                if self._in_bounds(nx, ny) and not self._visited[ny][nx]:
                    self.grid[y][x] &= ~wall_cur
                    self.grid[ny][nx] &= ~wall_nbr
                    self._visited[ny][nx] = True
                    stack.append((nx, ny))
                    moved = True
                    break

            if not moved:
                stack.pop()

    # ── Non-perfect mode: extra passages ───────────────────────────────────

    def _add_extra_passages(self, density: float = 0.2) -> None:
        """Add random extra passages to create loops in non-perfect mode.

        Iterates through all cells and randomly carves additional passages
        between visited cells, creating multiple solution paths. This is only
        called when perfect=False.
        """
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self._pattern_cells:
                    continue

                for dx, dy, wall_cur, wall_nbr in [
                    (1, 0, EAST, WEST),
                    (0, 1, SOUTH, NORTH),
                ]:
                    nx, ny = x + dx, y + dy

                    if not self._in_bounds(nx, ny):
                        continue
                    if (nx, ny) in self._pattern_cells:
                        continue
                    if not (self.grid[y][x] & wall_cur):
                        continue

                    if random.random() < density:
                        self.grid[y][x] &= ~wall_cur
                        self.grid[ny][nx] &= ~wall_nbr

    # ── 3×3 open area fix ─────────────────────────────────────────────────

    def _is_open_area(self, x: int, y: int) -> bool:
        """Return True if the 3×3 block at (x, y) has no interior walls."""
        for row in range(y, y + 3):
            for col in range(x, x + 3):
                if col + 1 < x + 3 and self.grid[row][col] & EAST:
                    return False
                if row + 1 < y + 3 and self.grid[row][col] & SOUTH:
                    return False
        return True

    def _fix_open_areas(self) -> None:
        """Add a South wall at the center of any fully open 3×3 block."""
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                if self._is_open_area(x, y):
                    cx, cy = x + 1, y + 1
                    if (cx, cy) not in self._pattern_cells:
                        if cy + 1 < self.height:
                            self.grid[cy][cx] |= SOUTH
                            self.grid[cy + 1][cx] |= NORTH

    # ── BFS solver ────────────────────────────────────────────────────────

    def _bfs_solve(self) -> str:
        """Find the shortest path from entry to exit using BFS.

        Returns:
            A string of N/E/S/W direction letters (shortest path),
            or an empty string if no path exists.
        """
        start = self.entry
        goal = self.exit_
        queue: deque[tuple[int, int]] = deque([start])
        came_from: dict[
            tuple[int, int], tuple[tuple[int, int], str] | None
            ] = {
            start: None
        }

        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break
            for dx, dy, wall, _ in DIRECTIONS:
                if self.grid[y][x] & wall:
                    continue
                nx, ny = x + dx, y + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in came_from:
                    continue
                came_from[(nx, ny)] = ((x, y), DIR_LETTER[(dx, dy)])
                queue.append((nx, ny))

        # Reconstruct path by walking came_from backwards
        if goal not in came_from:
            return ""
        path: list[str] = []
        current: tuple[int, int] = goal
        while came_from[current] is not None:
            prev, letter = came_from[current]  # type: ignore[misc]
            path.append(letter)
            current = prev
        path.reverse()
        return "".join(path)

    # ── Helper ─────────────────────────────────────────────────────────────

    def _in_bounds(self, x: int, y: int) -> bool:
        """Return True if (x, y) is inside the maze grid.

        Args:
            x: Column index.
            y: Row index.
        """
        return 0 <= x < self.width and 0 <= y < self.height
