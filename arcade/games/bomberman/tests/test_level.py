import pathlib, sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))

from arcade.games.bomberman.level import Level, EMPTY


def test_generate_random_deterministic():
    lvl1 = Level.generate_random(15, 13, seed=42)
    lvl2 = Level.generate_random(15, 13, seed=42)
    lvl3 = Level.generate_random(15, 13, seed=43)
    assert lvl1.grid == lvl2.grid
    assert lvl1.grid != lvl3.grid
    assert lvl1.grid[1][1] == EMPTY
    # ensure corridor path exists
    for x in range(1, lvl1.width - 1):
        assert lvl1.grid[1][x] == EMPTY
    for y in range(1, lvl1.height - 1):
        assert lvl1.grid[y][lvl1.width - 2] == EMPTY
