from dataclasses import dataclass


@dataclass
class Car:
    track: any
    z: float = 0.0
    x: float = 0.0  # lateral position (-1..1 roughly)
    speed: float = 0.0
    color: tuple = (0, 0, 255)

    max_speed: float = 220.0
    accel: float = 120.0
    brake: float = 160.0
    friction: float = 40.0

    def update(self, dt, controls, boost=False):
        if controls.get('accelerate'):
            self.speed += self.accel * dt * (1.5 if boost else 1.0)
        elif controls.get('brake'):
            self.speed -= self.brake * dt
        else:
            if self.speed > 0:
                self.speed -= self.friction * dt
            elif self.speed < 0:
                self.speed += self.friction * dt
        self.speed = max(-self.max_speed * 0.5, min(self.speed, self.max_speed))

        curve = self.track.curvature_at(self.z)
        if controls.get('left'):
            self.x -= 1.5 * dt * (self.speed / self.max_speed)
        if controls.get('right'):
            self.x += 1.5 * dt * (self.speed / self.max_speed)
        # push car to outside of curve
        self.x -= curve * 0.5 * (self.speed / self.max_speed)
        self.x = max(-3.0, min(self.x, 3.0))

        self.z = (self.z + self.speed * dt) % self.track.total_length


class Ghost:
    """Simple rubber-band opponent."""
    def __init__(self, track):
        self.track = track
        self.z = 20.0
        self.x = 0.0
        self.speed = 80.0
        self.color = (255, 0, 0)

    def update(self, dt, target_z):
        diff = self.track.relative_distance(self.z, target_z)
        base = 100.0
        self.speed = base + diff * 0.3
        self.z = (self.z + self.speed * dt) % self.track.total_length
