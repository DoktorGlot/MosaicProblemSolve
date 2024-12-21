class Vector:
    def __init__(self, x=0, y=0, marked=False):
        self.x = x
        self.y = y
        self.marked = marked

    @staticmethod
    def from_json(json):
        return Vector(json['x'], json['y'], json.get('marked', False))

    def set(self, v):
        self.x = v.x
        self.y = v.y
        return self

    def normalize(self):
        nl = self.length()
        return Vector(self.x / nl, self.y / nl)

    def add(self, v):
        return Vector(self.x + v.x, self.y + v.y)

    def sub(self, v):
        return Vector(self.x - v.x, self.y - v.y)

    def multiply_scalar(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.marked)

    def squared_length(self):
        dx = self.x * self.x
        dy = self.y * self.y
        return dx + dy

    def length(self):
        return (self.squared_length()) ** 0.5

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def cross(self, v):
        return self.y * v.x - self.x * v.y

    def perpendicular(self):
        return Vector(self.y, -self.x)

    def negative(self):
        return Vector(-self.x, -self.y)

    def translate(self, dx, dy):
        return Vector(self.x + dx, self.y + dy)

    def mark(self):
        self.marked = True
        return self

    def unmark(self):
        self.marked = False
        return self

    def approximately(self, v, tolerance=1e-9):
        return (abs(self.x - v.x) < tolerance) and (abs(self.y - v.y) < tolerance)

    def clone(self):
        return Vector(self.x, self.y, self.marked)
