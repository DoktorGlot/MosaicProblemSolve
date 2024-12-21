import sys
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP")
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
from part import Part
from bins import Bin
from polygon import Polygon
from vector import Vector
from placement import Placement
from util import createUniqueKey, toClipperCoordinates, toNestCoordinates, clipperScale, clipperThreshold, approximately, bounds
import pyclipper

def place(bins, parts, nfpCache):
    #print(nfpCache)
    # rotate paths by given rotation
    parts = [part.rotate(part.rotation) for part in parts]
    #print(vars(parts[0]))
    clipper = pyclipper.Pyclipper()
    allPlacements = []
    cost = 0
    #print(vars(bins[0]))
    for bin_ in bins:
        placed = []
        placements = []
        binArea = abs(pyclipper.Area([(bin_.points[0].x, bin_.points[0].y),(bin_.points[1].x, bin_.points[1].y),(bin_.points[2].x, bin_.points[2].y),(bin_.points[3].x, bin_.points[3].y)]))

        cost += 1  # cost for each new bin opened

        minWidth = None

        for part in parts:
            #print(part.id)
            #print(vars(part))
            # inner NFP
            key = createUniqueKey(bin_, part, False)
            #print(nfpCache)
            binNfp = nfpCache.get(key)
            #print('1:',binNfp)
            #print(vars(binNfp['result'][0]))
            # part unplaceable, skip
            if not binNfp or len(binNfp) <= 0:
                continue

            # ensure all necessary NFPs exist
            error = any(not nfpCache.get(createUniqueKey(p, part, False)) for p in placed)
            if error:
                continue

            # First placement, put it on the left
            if len(placed) <= 0:
                newPlacement = None
                #print(binNfp[nfp][0].points)
                for point in binNfp['result'][0].points:
                    #point = Vector.from_json(vars(point))
                    #print(point.x)
                    if not newPlacement or (point.x - part.points[0].x) < newPlacement.position.x:
                        newPlacement = Placement(bin_.id, part.id, point.sub(part.points[0]), part.rotation)
                        
                        
                #print(vars(newPlacement.position),newPlacement.rotation)
                placements.append(newPlacement)
                    #print(placements)
                placed.append(part)
                continue
            clipperBinNfp = []
            for j in binNfp:
                clipperBinNfp.append(toClipperCoordinates(binNfp[j][0].points))
            #print(placed)
            clipper = pyclipper.Pyclipper()
            for placedPart in placed:
                #print(vars(placedPart))
                key = createUniqueKey(placedPart, part, False)
                nfp = nfpCache.get(key)
                #print('2:',nfp)
                #print(nfp)
                if not nfp:
                    continue

                #print(nfp[nfp_item][0].points)
                clone = toClipperCoordinates(nfp['result'][0].points)
                for pt in range(0,len(clone)):
                    clone[pt]["X"] += placements[placed.index(placedPart)].position.x * clipperScale
                    clone[pt]["Y"] += placements[placed.index(placedPart)].position.y * clipperScale
                clone_transformed = [(point['X'], point['Y']) for point in clone]
                clone = pyclipper.CleanPolygon(clone_transformed, clipperThreshold)
                #print(clone)
                #clone = [{'X': p[0], 'Y': p[1]} for p in clone]
                #print(clone)
                    
                area = abs(pyclipper.Area(clone))
                if len(clone) > 2 and area > 0.1 * clipperScale * clipperScale:
                    clipper.AddPath(clone, pyclipper.PT_SUBJECT, True)

            
            combinedNfp = clipper.Execute(pyclipper.CT_UNION,pyclipper.PFT_NONZERO,pyclipper.PFT_NONZERO)
            #print(combinedNfp)
            if not combinedNfp:
                print('Failed to clip')
                continue


            clipper = pyclipper.Pyclipper()
            # Добавляем пути

            clipper.AddPaths(combinedNfp, pyclipper.PT_CLIP, True)
            
            clipperBinNfp = [[(int(point['X']), int(point['Y'])) for point in clipperBinNfp[0]]]
            clipper.AddPaths(clipperBinNfp, pyclipper.PT_SUBJECT, True)

            # Выполняем операцию разности (Difference)
            finalNfp = clipper.Execute(pyclipper.CT_DIFFERENCE,pyclipper.PFT_NONZERO,pyclipper.PFT_NONZERO)
            #print(finalNfp)
            if not finalNfp:
                print('Failed to clip 2')
                continue
            # Очистка полигонов
            finalNfp = pyclipper.CleanPolygons(finalNfp, clipperThreshold)
            #print('1:', finalNfp)
            # Фильтрация на основе длины и площади
            j = 0
            while j < len(finalNfp):
                
                polygon = finalNfp[j]
                #print('2:',polygon)
                area = abs(pyclipper.Area(polygon))
                if len(polygon) < 3 or area < 0.1 * clipperScale * clipperScale:
                    del finalNfp[j]  # Удаляем неподходящий полигон
                    j -= 1  # Переходим к следующему полигону
                j+=1

            # Проверяем результат
            if not finalNfp or len(finalNfp) <= 0:
                print('No valid final_nfp left')
                continue
            finalNfp = [[{'X': p[0], 'Y': p[1]} for p in finalNfp[0]]]
            #print(finalNfp)
            candidates = [Polygon(toNestCoordinates(f)) for f in finalNfp]
            

            newPlacement = None
            minArea = None
            minX = None
            for polygon in candidates:
                if abs(polygon.area()) < 2:
                    continue

                for point in polygon.points:
                    allPoints = []

                    for placedPart in placed:
                        placement = placements[placed.index(placedPart)]
                        #print(vars(placedPart))
                        for partPoint in placedPart.points:
                            #print(partPoint)
                            allPoints.append(partPoint.add(placement.position))
                    
                    shiftVector = Placement(bin_.id, part.id, point.sub(part.points[0]), part.rotation)
                    for p in part.points:
                        allPoints.append(p.add(shiftVector.position))
                    bb = bounds(allPoints)

                    # weigh width more, to help compress in direction of gravity
                    area = bb.width * 2 + bb.height
                    if minArea == None or area < minArea or (approximately(minArea, area) and (minX == None or shiftVector.position.x < minX)):
                        newPlacement = shiftVector
                        #print(newPlacement, part.id)
                        minArea = area
                        minWidth = bb.width * bb.height
                        minX = shiftVector.position.x

            if newPlacement is not None:
                placements.append(newPlacement)
                placed.append(part)

        if minWidth is not None:
            cost += minWidth / binArea

        # Remove placed parts from unplaced
        for item in placed:
            if item in parts:
                parts.remove(item)

        if placements and len(placements) > 0:
            allPlacements.extend(placements)
    #print(placements)
    # There were parts that couldn't be placed
    cost += 2 * len(parts)
    #print(allPlacements)
    #print(parts)
    return {'placements': allPlacements, 'cost': cost, 'unplaced': parts}


# Worker handling function (assuming message comes from a worker context)
def postMessage(data):
    # Проверяем, являются ли объекты уже экземплярами классов Bin и Part
    bins = [ 
        bin_ for bin_ in data['bins']
    ]
    parts = [
        part for part in data['parts']
    ]
    #print(vars(parts[0]))
    # Вызываем функцию place с уже созданными объектами
    result = place(bins, parts, data['nfpCache'])
    #for i in result['placements']:
        #print(vars(i))
    return {'result': result}
