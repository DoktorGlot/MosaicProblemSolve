import sys
import asyncio
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP")
from part import Part
from util import noFitRectanglePolygon, noFitPolygon, minkowskiDifference

async def addEventListener(event_data):
    pa = Part.from_json(vars(event_data['A']))

    pa = pa.rotate(pa.rotation)
    pb = Part.from_json(vars(event_data['B']))
    pb = pb.rotate(pb.rotation)
    debug = event_data.get('debug', False)
    result = []
    if hasattr(event_data['A'], 'isBin') and event_data['A'].isBin:
        polygon = noFitRectanglePolygon(pa, pb, event_data['inside'], event_data['edges'])
        if polygon:
            result = [polygon]
    else:
        if event_data.get('edges', False):
            result = noFitPolygon(pa, pb, event_data['inside'], event_data['edges'], debug)
        else:
            result = [minkowskiDifference(pa, pb)]
    for i in range(0,len(result)):
        if result[i].area() > 0:
            result[i] = result[i].points.reverse()
    return {'result': result}
