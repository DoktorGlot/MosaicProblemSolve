import sys
import json
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
from part import Part
from vector import Vector

class Bin(Part):
    def __init__(self, id, width, height, options):
        points = [
            Vector(0, 0),
            Vector(width, 0),
            Vector(width, height),
            Vector(0, height)
        ]
        super().__init__(id, points, options)
        self.width = width
        self.height = height
        self.isBin = True

    @staticmethod
    def from_json(json):
        bin_ = Bin(json['id'], json['width'], json['height'], json['options'])
        bin_.offset = Vector(json['offset']['x'], json['offset']['y']) if 'offset' in json else Vector(0, 0)
        bin_.rotation = json.get('rotation', 0)
        bin_.groupId = json.get('groupId')
        return bin_

    def clone(self):
        bin_ = Bin(self.id, self.width, self.height, self.options)
        bin_.offset = Vector(self.offset.x, self.offset.y)
        bin_.rotation = self.rotation
        bin_.groupId = self.groupId
        return bin_

    def __str__(self):
        return f"bin:{self.id}"