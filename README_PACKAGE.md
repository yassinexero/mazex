# mazegen

Reusable maze generator using Recursive Backtracker (DFS).

## Installation

pip install mazegen-1.0.0-py3-none-any.whl

## Quick start

from mazegen import MazeGenerator

gen = MazeGenerator(width=20, height=15, entry=(0,0), exit_=(19,14), seed=42)
gen.generate()

print(gen.grid)      # 2D list of wall bitmasks
print(gen.solution)  # "EESSENWW..." shortest path
print(gen.entry)     # (0, 0)
print(gen.exit_)     # (19, 14)

## Parameters

- width, height — maze dimensions
- entry, exit_ — (x,y) tuples
- perfect — True = one path only, False = loops allowed
- seed — integer for reproducible generation
