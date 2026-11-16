# Cellular Automata

A Conway's **Game of Life** simulation that runs endlessly: a 60×60 toroidal grid seeded with a
random soup plus a few classic spaceships, animated live in a Matplotlib window until you close it.

## Technologies

| Tool | Role in the project |
| --- | --- |
| **Python** | The whole project — one script, `main.py`. |
| **[cellpylib](https://pypi.org/project/cellpylib/)** | Cellular-automata library: grid initialisation (`init_random2d`), the evolution engine (`evolve2d`) and the built-in `game_of_life_rule`. |
| **NumPy** | The grid is a NumPy `int32` array; used for seeding patterns and comparing consecutive generations. |
| **Matplotlib** | Rendering and animation (`matshow` + `FuncAnimation`). |
| **Git / GitHub** | Version control and hosting. |

No GUI framework, no build step — a single dependency-light script.

---

## Features

- **Runs forever.** The evolution is driven by a generator (`evolve_forever`) that never returns, so
  the animation is not a fixed 250-step recording — it keeps computing new generations as you watch.
- **Chunked computation.** Generations are produced in blocks of `CHUNK` (25 at a time) so the setup
  cost of each `evolve2d` call is amortised and the window never stalls on a long pre-compute.
- **Toroidal board.** cellpylib wraps the neighbourhood indices, so gliders leave one edge and come
  back on the other instead of dying at the border.
- **Auto-reseed on stasis.** Random soup eventually settles into still lifes; if the field is
  unchanged for `STASIS_LIMIT` generations, a fresh soup is dropped in so the animation stays alive.
- **Classic patterns.** Glider, blinker and lightweight spaceship are stamped into the soup at fixed
  anchors; set `PATTERNS = None` for pure random soup.
- **Live stats caption.** The title shows the generation count and how many cells are currently alive.
- **Everything is configurable** from one block at the top of the file:

  | Setting | Meaning |
  | --- | --- |
  | `ROWS`, `COLS` | Grid size (default 60×60). |
  | `INTERVAL_MS` | Milliseconds per generation (30 ≈ 33 fps; raise it if the window stutters). |
  | `CHUNK` | Generations computed per `evolve2d` call. |
  | `MEMOIZE` | Cache rule results per neighbourhood pattern (`True` ≈ 35 % faster). |
  | `SEED` | Set to an `int` for a reproducible soup. |
  | `PATTERNS` | Which spaceships to place, or `None`. |
  | `RESEED_ON_STASIS`, `STASIS_LIMIT` | Freeze detection and reseeding. |
  | `CMAP` | Colour map (`'binary'`, `'Greys'`, `'magma'`, …). |

---

## The process

**Where it started.** The first version pre-computed a fixed 250-generation history with one
`cpl.evolve2d(...)` call and animated that array. That worked, but it meant a ~5 second wait before
anything appeared, and the animation stopped after 250 frames.

**What I learned.**

- *Pre-computing everything is a trap.* Turning the run into a **generator** that yields states as
  they are computed removed the startup wait and made "forever" possible. `FuncAnimation` accepts an
  iterator for `frames`, so an endless generator is all it takes — with `cache_frame_data=False`,
  otherwise Matplotlib tries to cache frames we can never finish collecting.
- *`evolve2d` is chunkable.* It accepts a history tensor whose **last layer is the starting
  condition**, so feeding back the last frame of a chunk resumes the same evolution. That is what
  makes the endless loop cheap (~21 ms per generation on a 60×60 board).
- *Blitting.* Returning the artists from the update function with `blit=True` makes Matplotlib reuse
  the background instead of repainting the whole figure. The animation object must also be kept in a
  variable, or garbage collection silently kills the loop.
- *Memoization.* `memoize=True` caches the rule result per neighbourhood pattern; since Life has only
  512 possible neighbourhoods, the cache fills up almost immediately and pays for itself.
- *Edge behaviour matters.* cellpylib wraps indices at the borders (torus), which is why spaceships
  keep travelling instead of running off the board — worth knowing before you interpret a pattern.
- *Debugging my own code.* The original file had two animation setups (`imshow` and `matshow`) with
  two `animate` functions, where the second overrode the first but `init_func` still updated the
  unused artist. Cleaning that up taught me to keep exactly one render path.

**How the creation went.** Incrementally: get a static frame on screen, then a fixed-length loop,
then the generator, then the wrap-around/stasis behaviour and the config block. Testing headless with
the `Agg` backend (driving the animation frames without opening a window) was the fastest way to
measure frame cost, since it gives the same code path without a GUI.

---

## Running the project

Requires **Python 3.10+**.

```bash
git clone https://github.com/Unknown-S48/Cellular-Automata.git
cd Cellular-Automata
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python main.py
```

A window opens and the simulation starts immediately; it runs until you close the window.

**Notes**

- If the animation stutters, raise `INTERVAL_MS` (e.g. `60`) or shrink `ROWS`/`COLS`; the rule loop is
  pure Python, so cost grows roughly with `ROWS * COLS`.
- For a reproducible run, set `SEED = 1`.
- `matplotlib` needs a GUI backend to show a window. On a headless machine, install a backend you
  have (`matplotlib.backends.backend_qt5agg`) or save frames instead of showing them.
- To export a GIF, keep the same generator but call
  `ani.save("demo.gif", writer="pillow", fps=1000 // INTERVAL_MS)` in place of `plt.show()`
  (needs `pip install pillow`, and remember it would run forever — pass a limited number of frames).

---

## Ideas to build on this

- Other rules: HighLife, Seeds, Day & Night, Wireworld — cellpylib ships many of them.
- A vectorised NumPy rule (convolution-based neighbour count) instead of the per-cell Python loop.
- Click-to-draw cells, a pause/play button, a live population graph.
- Save a space-time diagram with `cpl.plot2d_spacetime`.
