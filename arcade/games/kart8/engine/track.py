import random
from dataclasses import dataclass


@dataclass
class Segment:
    length: float = 10.0
    curvature: float = 0.0
    elevation: float = 0.0
    width: float = 1.0


class Track:
    """Represents a looping track made of simple segments."""

    def __init__(self):
        self.segments = []
        self.cumulative = []
        self.total_length = 0.0
        self.billboards = []  # list of (z, x, color)
        self.items = []  # list of dicts with keys type,z,x,speed etc
        # checkpoints are stored as distances along the track (z positions)
        # that must be passed in order for a lap to be counted.  ``check_width``
        # defines the lateral tolerance from the centre of the road.
        self.checkpoints = []
        self.check_width = 3.0

    def add(self, seg: Segment):
        self.segments.append(seg)
        self.total_length += seg.length
        self.cumulative.append(self.total_length)

    def segment_at(self, z):
        """Return segment and its start position for distance *z*."""
        if not self.segments:
            return None, 0.0, 0.0
        z = z % self.total_length
        prev_end = 0.0
        for seg, end in zip(self.segments, self.cumulative):
            if z <= end:
                return seg, prev_end, (z - prev_end) / seg.length
            prev_end = end
        seg = self.segments[-1]
        start = self.cumulative[-2] if len(self.cumulative) > 1 else 0.0
        return seg, start, 1.0

    def curvature_at(self, z):
        seg, _, _ = self.segment_at(z)
        return seg.curvature if seg else 0.0

    def relative_distance(self, z, target):
        diff = target - z
        if diff < 0:
            diff += self.total_length
        return diff

    # -- checkpoint helpers -------------------------------------------------
    def passed(self, prev_z: float, new_z: float, cp_z: float) -> bool:
        """Return True if the interval [prev_z, new_z] crosses ``cp_z``.

        The track loops so wrap‑around is handled correctly.
        """

        if prev_z <= new_z:
            return prev_z <= cp_z < new_z
        # wrapped around end of track
        return cp_z >= prev_z or cp_z < new_z


def create_demo_track():
    track = Track()
    # straight
    track.add(Segment(length=100, curvature=0, width=1.0))
    # gentle right curve
    track.add(Segment(length=100, curvature=0.002, width=1.0))
    # hill
    track.add(Segment(length=80, curvature=0, elevation=10, width=1.0))
    # left curve
    track.add(Segment(length=120, curvature=-0.003, width=1.0))
    # flat straight
    track.add(Segment(length=100, curvature=0, width=1.0))

    # add some billboards along track
    colors = [(0, 200, 0), (0, 180, 0), (0, 150, 0)]
    spacing = track.total_length / 20
    for i in range(20):
        z = i * spacing
        x = random.choice([-2.0, 2.0])
        color = random.choice(colors)
        track.billboards.append((z, x, color))

    # place a few items along the track
    track.items = []
    for i in range(3):
        track.items.append({"type": "boost", "z": 30 + i * 80, "x": 0.0})
    for i in range(2):
        track.items.append({"type": "oil", "z": 70 + i * 120, "x": 1.5})
    track.items.append(
        {"type": "shell", "z": 150, "x": -0.5, "speed": 90.0, "active": True}
    )

    # set up a few checkpoints evenly spaced around the track
    track.checkpoints = [0.0]
    num_cp = 3
    spacing = track.total_length / num_cp
    for i in range(1, num_cp):
        track.checkpoints.append(i * spacing)
    track.check_width = 2.5
    return track
