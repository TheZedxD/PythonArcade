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
    return track
