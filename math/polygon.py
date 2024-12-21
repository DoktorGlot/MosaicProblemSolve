from svg import Svg
from vector import Vector
from bounding_box import BoundingBox
import math

class Polygon(Svg):

    def __init__(self, points, options=None):
        super().__init__()
        self.points = points
        self.options = options or {}
        self.group_id = ''

    @staticmethod
    def from_json(json):
        points = [Vector.from_json(p) for p in json['points']]
        poly = Polygon(points, json.get('options', {}))
        poly.group_id = json.get('groupId', '')
        return poly

    def bounds(self):
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')

        for p in self.points:
            min_x = min(p.x, min_x)
            min_y = min(p.y, min_y)
            max_x = max(p.x, max_x)
            max_y = max(p.y, max_y)

        return BoundingBox(Vector(min_x, min_y), Vector(max_x, max_y))

    def translate(self, dx, dy):
        np = self.clone()
        np.points = [p.translate(dx, dy) for p in np.points]
        return np

    def rotate(self, angle=0):
        np = self.clone()
        sin_angle = math.sin(angle)
        cos_angle = math.cos(angle)
        np.points = [
            Vector(p.x * cos_angle - p.y * sin_angle, p.x * sin_angle + p.y * cos_angle, p.marked)
            for p in np.points
        ]
        return np

    def clone(self):
        points = [p.clone() for p in self.points]
        np = Polygon(points, self.options)
        np.group_id = self.group_id
        return np

    def area(self):
        area = 0
        n = len(self.points)
        for i in range(n):
            j = (i - 1) % n  # Wrap around
            area += (self.points[j].x + self.points[i].x) * (self.points[j].y - self.points[i].y)
        return 0.5 * area

    def approximately(self, other):
        if len(self.points) != len(other.points):
            return False
        return all(p0.approximately(p1) for p0, p1 in zip(self.points, other.points))
