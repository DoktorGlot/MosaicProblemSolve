import math
import sys
import copy
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
from vector import Vector
from polygon import Polygon

class Part(Polygon):
    def __init__(self, id, points, options):
        super().__init__(points, options)
        self.id = id
        self.offset = Vector(0, 0)
        self.transformed = 0
        self.rotation = 0

    @staticmethod
    def from_json(json):
        # Используем объекты Vector напрямую, если они уже есть
        points = [p if isinstance(p, Vector) else Vector.from_json(p) for p in json['points']]
        # Создаём объект Part
        part = Part(json['id'], points, json['options'])

        # Обработка offset
        if 'offset' in json:
            offset_data = json['offset']
            part.offset = Vector(vars(offset_data)['x'],vars(offset_data)['y'])
        else:
            part.offset = Vector(0, 0)

        # Присваиваем оставшиеся свойства
        part.transformed = json.get('transformed', 0)
        part.rotation = json.get('rotation', 0)
        part.group_id = json.get('groupId', None)
        
        return part

    def transform(self, index, range_):
        cloned = self.clone()
        cloned.transformed = index
        cloned.rotation = (index / range_) * math.pi * 2
        return cloned

    def clone(self):
        points = [p.clone() for p in self.points]
        np = Part(self.id, points, self.options)
        np.offset = self.offset.clone()
        np.transformed = self.transformed
        np.rotation = self.rotation
        np.group_id = self.group_id
        return np

    def __str__(self):
        return f'{self.group_id}:{self.transformed}'
