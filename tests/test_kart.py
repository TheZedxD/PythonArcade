from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "arcade")])

from arcade.games.kart8.engine.track import create_demo_track  # noqa: E402
from arcade.games.kart8.engine.physics import Car  # noqa: E402
from arcade.games.kart8.game import NUM_LAPS  # noqa: E402


def test_deterministic_physics():
    """Updating with different dt slices should give identical results."""

    track = create_demo_track()

    car1 = Car(track)
    for _ in range(10):  # coarse steps
        car1.update(0.1, {"accelerate": True}, False)
    speed1 = car1.speed

    car2 = Car(track)
    for _ in range(50):  # fine steps
        car2.update(0.02, {"accelerate": True}, False)

    # identical acceleration regardless of step size
    assert abs(speed1 - car2.speed) < 1e-5

    # braking brings the kart to (almost) a halt
    for _ in range(120):
        car1.update(1 / 60, {"brake": True}, False)
    assert car1.speed <= 0.1


def test_checkpoint_lap_and_finish():
    """A car travelling at max speed should complete the required laps."""

    track = create_demo_track()
    car = Car(track)
    cp_index = 0
    laps = 0
    dt = 1 / 60

    # enough frames to cover the track for the number of laps
    frames = int((track.total_length / car.max_speed) * 60) * NUM_LAPS + 60
    for _ in range(frames):
        prev_z = car.z
        car.update(dt, {"accelerate": True}, False)
        next_cp = track.checkpoints[(cp_index + 1) % len(track.checkpoints)]
        if abs(car.x) <= track.check_width and track.passed(prev_z, car.z, next_cp):
            cp_index = (cp_index + 1) % len(track.checkpoints)
            if cp_index == 0:
                laps += 1

    assert laps >= NUM_LAPS
