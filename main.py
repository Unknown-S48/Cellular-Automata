"""Conway's Game of Life, running forever on a toroidal grid.
cellpylib wraps the grid edges, so the board behaves like a torus. The animation
never ends, and the soup is reseeded automatically if the field ever freezes.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cellpylib as cpl
import numpy as np

# config
ROWS = 60                   # grid height
COLS = 60                   # grid width
INTERVAL_MS = 30            # milliseconds between generations (~33 fps)
CHUNK = 25                  # generations computed per evolve2d call
MEMOIZE = True              # cache rule results per neighbourhood pattern
SEED = None                 # int for a reproducible soup, None for a fresh one per run
PATTERNS = ("glider", "blinker", "lwss")   # stamped onto the soup, None for pure soup
RESEED_ON_STASIS = True     # reseed once the field stops changing
STASIS_LIMIT = 20           # consecutive frozen generations before reseeding
CMAP = "binary"             # 'binary', 'Greys', 'magma', ...

# Each pattern is a list of (row, column) offsets from an anchor point.
SHIPS = {
    "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "blinker": [(0, 1), (1, 1), (2, 1)],
    "lwss": [(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)],
}

# seeding
def seed_grid(*, soup=True, ships=PATTERNS, seed=SEED):
    """One starting generation: a random soup with the classic spaceships in it."""
    if seed is not None:
        np.random.seed(seed)

    grid = np.random.randint(2, size=(ROWS, COLS), dtype=np.int32) if soup else np.zeros((ROWS, COLS), np.int32)

    if ships:
        anchors = [(ROWS // 2, COLS // 5), (ROWS // 3, COLS // 2), (ROWS // 4, 3 * COLS // 5)]
        for ship, (row, col) in zip(ships, anchors):
            for dr, dc in SHIPS[ship]:
                grid[(row + dr) % ROWS, (col + dc) % COLS] = 1

    return grid

# evolution
def evolve_forever():
    """Yield (generation, state) pairs forever, computing CHUNK generations at a time.

    evolve2d expects a (timesteps, rows, cols) tensor whose last layer is the starting
    condition and returns the whole chunk, so we feed it the current state and keep the
    last layer as the seed of the next chunk. That amortises the setup cost of each call
    over CHUNK generations (~21 ms per generation on a 60x60 board).
    """
    state = seed_grid()
    previous = state
    generation = 0
    frozen_for = 0

    while True:
        history = cpl.evolve2d(
            state[np.newaxis, :, :],
            timesteps=CHUNK + 1,
            neighbourhood="Moore",
            memoize=MEMOIZE,
            apply_rule=cpl.game_of_life_rule,
        )

        for frame in history[1:]:
            generation += 1
            frozen_for = frozen_for + 1 if np.array_equal(frame, previous) else 0
            previous = frame
            yield generation, frame

            if RESEED_ON_STASIS and frozen_for >= STASIS_LIMIT:
                frozen_for = 0
                state = seed_grid()
                previous = state
                break
        else:
            # no reseed happened: continue from the end of this chunk
            state = history[-1]
            previous = state

# animation
def build_animation():
    """Wire the endless generator up to a matplotlib animation."""
    fig, ax = plt.subplots()
    ax.set_axis_off()

    generator = evolve_forever()
    _, first = next(generator)

    board = ax.matshow(first, cmap=CMAP, interpolation="nearest")
    caption = ax.set_title("gen      0 | live     0")

    def update(frame):
        generation, state = frame
        board.set_data(state)
        caption.set_text(f"gen {generation:>6} | live {int(state.sum()):>5}")
        return [board, caption]

    # frames is an endless iterator, so FuncAnimation simply never runs out of them.
    ani = animation.FuncAnimation(
        fig, update, frames=generator, interval=INTERVAL_MS, blit=True, cache_frame_data=False
    )
    return fig, ani

def main():
    fig, ani = build_animation()   # keep a reference, or the animation is garbage collected
    plt.show()

if __name__ == "__main__":
    main()