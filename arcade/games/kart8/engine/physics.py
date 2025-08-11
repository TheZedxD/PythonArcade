"""Basic deterministic physics for the kart game.

The previous implementation updated the car directly using the variable
``dt`` passed in from the main loop.  This meant that the behaviour of the
car was tied to the frame rate and small variations in ``dt`` would produce
different results.  The tests for this kata require deterministic physics so
that a sequence of smaller time steps results in exactly the same state as a
single large step.

The :class:`Car` class below implements a fixed time‑step accumulator.  Calls
to :meth:`update` simply accumulate time and repeatedly step the simulation
in ``1/60`` second increments.  Each step applies forward acceleration and
drag, lateral movement with side friction and optional drifting.  Steering
sensitivity decreases with speed so that karts are easier to control at low
velocity and harder to turn at top speed.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Car:
    track: Any
    z: float = 0.0
    x: float = 0.0  # lateral position
    speed: float = 0.0  # forward speed
    vx: float = 0.0  # lateral velocity
    color: tuple = (0, 0, 255)
    oil_timer: float = 0.0

    # Tunable parameters
    max_speed: float = 220.0
    accel: float = 120.0
    brake: float = 160.0
    drag: float = 40.0
    side_friction: float = 8.0
    steer_power: float = 2.0

    # Drift handling
    drift_boost: float = 40.0
    drift_cooldown: float = 0.0
    _drift_timer: float = 0.0

    # Fixed step accumulator.  A 16 ms step closely matches a 60 FPS
    # update rate while still allowing small dt fluctuations from the main
    # loop without drifting over time.
    _accum: float = 0.0
    step_dt: float = 0.016

    def update(self, dt, controls, drift=False):
        """Advance the simulation by *dt* seconds.

        A fixed time step is used internally so that physics remain
        deterministic regardless of the size of ``dt`` provided by the game
        loop.  ``controls`` is a mapping with ``accelerate``, ``brake``,
        ``left`` and ``right`` booleans.  ``drift`` is True while the drift
        key is held down which temporarily increases the turn rate and grants
        a small speed boost when released.
        """

        self._accum += dt
        while self._accum >= self.step_dt:
            self._step(self.step_dt, controls, drift)
            self._accum -= self.step_dt

    # ------------------------------------------------------------------
    def _step(self, dt, controls, drift):
        # --- grip & drift cooldown ---
        if self.oil_timer > 0:
            self.oil_timer = max(0.0, self.oil_timer - dt)
            grip = 0.3
        else:
            grip = 1.0
        if self.drift_cooldown > 0:
            self.drift_cooldown = max(0.0, self.drift_cooldown - dt)

        # --- forward acceleration / braking ---
        if controls.get("accelerate"):
            self.speed += self.accel * dt
        elif controls.get("brake"):
            self.speed -= self.brake * dt
        else:
            if self.speed > 0:
                self.speed = max(0.0, self.speed - self.drag * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + self.drag * dt)
        self.speed = max(-self.max_speed * 0.5, min(self.speed, self.max_speed))

        # --- steering ---
        steer = 0.0
        if controls.get("left"):
            steer -= 1.0
        if controls.get("right"):
            steer += 1.0
        if steer:
            sensitivity = max(0.2, 1.0 - abs(self.speed) / self.max_speed)
            steer *= self.steer_power * sensitivity * grip
            if drift:
                steer *= 1.5
            self.vx += steer * dt

        # --- drift boost ---
        drifting = drift and steer != 0 and self.drift_cooldown <= 0
        if drifting:
            # accumulate drift time in vx (no storage needed)
            self.vx *= 1.02
            self._drift_timer += dt
        else:
            if self._drift_timer > 0 and self.drift_cooldown <= 0:
                self.speed = min(
                    self.max_speed * 1.2, self.speed + self.drift_boost
                )
                self.drift_cooldown = 1.0
            self._drift_timer = 0.0

        # --- lateral friction & curvature ---
        self.vx -= self.vx * self.side_friction * dt
        curve = self.track.curvature_at(self.z)
        self.vx -= curve * (self.speed / self.max_speed)
        self.x += self.vx * dt

        # collision / walls
        if self.x < -3.0:
            self.x = -3.0
            self.vx = 0.0
        elif self.x > 3.0:
            self.x = 3.0
            self.vx = 0.0

        # --- advance along track ---
        self.z = (self.z + self.speed * dt) % self.track.total_length


class Ghost:
    """Simple rubber-band opponent."""

    def __init__(self, track, difficulty: float = 1.0):
        self.track = track
        self.z = 20.0
        self.x = 0.0
        self.speed = 80.0
        self.color = (255, 0, 0)
        self.difficulty = difficulty

    def update(self, dt, target_z):
        diff = self.track.relative_distance(self.z, target_z)
        base = 100.0 * self.difficulty
        self.speed = base + diff * 0.3 * self.difficulty
        self.z = (self.z + self.speed * dt) % self.track.total_length
