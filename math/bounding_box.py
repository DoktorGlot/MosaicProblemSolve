class BoundingBox:

    def __init__(self, min_point, max_point):
        self.min = min_point
        self.max = max_point
        self.width = vars(self.max)['x'] - vars(self.min)['x']
        self.height = vars(self.max)['y'] - vars(self.min)['y']
