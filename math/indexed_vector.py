from vector import Vector

class IndexedVector(Vector):

    def __init__(self, x, y, start, end):
        super().__init__(x, y)
        self.start = start
        self.end = end

    def clone(self):
        cloned = super().clone()
        cloned.start = self.start.clone()
        cloned.end = self.end.clone()
        return cloned
