import sys
import json
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
import pyclipper  # Assuming you have a Python wrapper for ClipperLib
from vector import Vector  # Assuming a custom Vector class is defined in the math/vector module
from indexed_vector import IndexedVector  # Assuming a custom IndexedVector class is defined in the math/indexed_vector module
from polygon import Polygon  # Assuming a custom Polygon class is defined in the math/polygon module
from bounding_box import BoundingBox
TOL = 1e-9

clipperScale = 1e7
clipperThreshold = 0.0001 * clipperScale

def toClipperCoordinates(points):
    result = [{'X': p.x * clipperScale, 'Y': p.y * clipperScale} for p in points]
    return result

def toNestCoordinates(path):
    return [Vector(p['X'] / clipperScale, p['Y'] / clipperScale) for p in path]

def approximately(a, b, tolerance=TOL):
    return abs(a - b) < tolerance

def bounds(points):
    minX = float('inf')
    maxX = float('-inf')
    minY = float('inf')
    maxY = float('-inf')

    for p in points:
        minX = min(p.x, minX)
        minY = min(p.y, minY)
        maxX = max(p.x, maxX)
        maxY = max(p.y, maxY)

    return BoundingBox(Vector(minX, minY), Vector(maxX, maxY))

# returns true if p lies on the line segment defined by AB, but not at any endpoints
# may need work!
def onSegmen(A, B, p):
    # vertical line
    if approximately(A.x, B.x) and approximately(p.x, A.x):
        if not approximately(p.y, B.y) and not approximately(p.y, A.y) and min(B.y, A.y) < p.y < max(B.y, A.y):
            return True
        else:
            return False

    # horizontal line
    if approximately(A.y, B.y) and approximately(p.y, A.y):
        if not approximately(p.x, B.x) and not approximately(p.x, A.x) and min(B.x, A.x) < p.x < max(B.x, A.x):
            return True
        else:
            return False

    # range check
    if (p.x < A.x and p.x < B.x) or (p.x > A.x and p.x > B.x) or (p.y < A.y and p.y < B.y) or (p.y > A.y and p.y > B.y):
        return False

    # exclude endpoints
    if (approximately(p.x, A.x) and approximately(p.y, A.y)) or (approximately(p.x, B.x) and approximately(p.y, B.y)):
        return False

    cross = (p.y - A.y) * (B.x - A.x) - (p.x - A.x) * (B.y - A.y)

    if abs(cross) > TOL:
        return False

    dot = (p.x - A.x) * (B.x - A.x) + (p.y - A.y) * (B.y - A.y)

    if dot < 0 or approximately(dot, 0):
        return False

    len2 = (B.x - A.x) ** 2 + (B.y - A.y) ** 2

    if dot > len2 or approximately(dot, len2):
        return False

    return True
def pointInPolygon(point, polygon):
    if not polygon or len(polygon.points) < 3:
        return None

    inside = False
    n = len(polygon.points)

    for i in range(n):
        j = (i - 1) % n
        pi = polygon.points[i].add(polygon.offset)
        pj = polygon.points[j].add(polygon.offset)

        if pi.approximately(point):
            return None  # no result

        if on_segment(pi, pj, point):
            return None  # exactly on the segment

        if pi.approximately(pj):
            continue  # ignore very small lines

        intersected = ((pi.y > point.y) != (pj.y > point.y)) and \
                      (point.x < (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y) + pi.x)

        if intersected:
            inside = not inside

    return inside


def pointDistance(p, s1, s2, normal, infinite=False):
    normal = normal.normalize()

    dir = normal.perpendicular()

    pdot = p.dot(dir)
    s1dot = s1.dot(dir)
    s2dot = s2.dot(dir)

    pdotnorm = p.dot(normal)
    s1dotnorm = s1.dot(normal)
    s2dotnorm = s2.dot(normal)

    if not infinite:
        if ((pdot < s1dot or abs(pdot - s1dot) < 1e-9) and (pdot < s2dot or abs(pdot - s2dot) < 1e-9)) or \
           ((pdot > s1dot or abs(pdot - s1dot) < 1e-9) and (pdot > s2dot or abs(pdot - s2dot) < 1e-9)):
            return None  # dot doesn't collide with segment, or lies directly on the vertex

        if abs(pdot - s1dot) < 1e-9 and abs(pdot - s2dot) < 1e-9:
            if pdotnorm > s1dotnorm and pdotnorm > s2dotnorm:
                return min(pdotnorm - s1dotnorm, pdotnorm - s2dotnorm)
            if pdotnorm < s1dotnorm and pdotnorm < s2dotnorm:
                return -min(s1dotnorm - pdotnorm, s2dotnorm - pdotnorm)

    return -(pdotnorm - s1dotnorm + (s1dotnorm - s2dotnorm) * (s1dot - pdot) / (s1dot - s2dot))
def segmentDistance(A, B, E, F, direction):
    normal = direction.perpendicular()

    dotA = A.dot(normal)
    dotB = B.dot(normal)
    dotE = E.dot(normal)
    dotF = F.dot(normal)

    crossA = A.cross(direction)
    crossB = B.cross(direction)
    crossE = E.cross(direction)
    crossF = F.cross(direction)

    ABmin = min(dotA, dotB)
    ABmax = max(dotA, dotB)

    EFmax = max(dotE, dotF)
    EFmin = min(dotE, dotF)

    # Segments that will merely touch at one point
    if approximately(ABmax, EFmin) or approximately(ABmin, EFmax):
        return None

    # Segments miss each other completely
    if ABmax < EFmin or ABmin > EFmax:
        return None

    overlap = None
    if (ABmax > EFmax and ABmin < EFmin) or (EFmax > ABmax and EFmin < ABmin):
        overlap = 1
    else:
        minMax = min(ABmax, EFmax)
        maxMin = max(ABmin, EFmin)

        maxMax = max(ABmax, EFmax)
        minMin = min(ABmin, EFmin)

        overlap = (minMax - maxMin) / (maxMax - minMin)

    ae = E.sub(A)
    ab = B.sub(A)
    af = F.sub(A)
    ef = E.sub(F)

    crossABE = ae.cross(ab)
    crossABF = af.cross(ab)

    # Lines are collinear
    if approximately(crossABE, 0) and approximately(crossABF, 0):
        ABnorm = ab.perpendicular().normalize()
        EFnorm = ef.perpendicular().normalize()

        # Segment normals must point in opposite directions
        if abs(ABnorm.cross(EFnorm)) < TOL and ABnorm.dot(EFnorm) < 0:
            # Normal of AB segment must point in the same direction as given direction vector
            normdot = ABnorm.dot(direction)
            # The segments merely slide along each other
            if approximately(normdot, 0):
                return None

            if normdot < 0:
                return 0

        return None

    distances = []

    reverse = direction.negative()

    # Coincident points
    if approximately(dotA, dotE):
        distances.append(crossA - crossE)
    elif approximately(dotA, dotF):
        distances.append(crossA - crossF)
    elif EFmin < dotA < EFmax:
        d = point_distance(A, E, F, reverse)
        if d is not None and approximately(d, 0):  # A currently touches EF, but AB is moving away from EF
            dB = point_distance(B, E, F, reverse, True)
            if dB < 0 or approximately(dB * overlap, 0):
                d = None
        if d is not None:
            distances.append(d)

    if approximately(dotB, dotE):
        distances.append(crossB - crossE)
    elif approximately(dotB, dotF):
        distances.append(crossB - crossF)
    elif EFmin < dotB < EFmax:
        d = point_distance(B, E, F, reverse)
        if d is not None and approximately(d, 0):  # crossA > crossB, A currently touches EF, but AB is moving away from EF
            dA = point_distance(A, E, F, reverse, True)
            if dA < 0 or approximately(dA * overlap, 0):
                d = None
        if d is not None:
            distances.append(d)

    if ABmin < dotE < ABmax:
        d = point_distance(E, A, B, direction)
        if d is not None and approximately(d, 0):  # crossF < crossE, A currently touches EF, but AB is moving away from EF
            dF = point_distance(F, A, B, direction, True)
            if dF < 0 or approximately(dF * overlap, 0):
                d = None
        if d is not None:
            distances.append(d)

    if ABmin < dotF < ABmax:
        d = point_distance(F, A, B, direction)
        if d is not None and approximately(d, 0):  # crossE < crossF, A currently touches EF, but AB is moving away from EF
            dE = point_distance(E, A, B, direction, True)
            if dE < 0 or approximately(dE * overlap, 0):
                d = None
        if d is not None:
            distances.append(d)

    if not distances:
        return None

    return min(distances)
def polygonSlideDistance(A, B, direction, ignore_negative=False):
    AP = A.points[:]
    BP = B.points[:]

    # Close the loop for polygons
    if AP[0] != AP[-1]:
        AP.append(AP[0])

    if BP[0] != BP[-1]:
        BP.append(BP[0])

    distance = None
    dir = direction.normalize()

    for i in range(len(BP) - 1):
        for j in range(len(AP) - 1):
            A1 = AP[j].add(A.offset)
            A2 = AP[j + 1].add(A.offset)
            B1 = BP[i].add(B.offset)
            B2 = BP[i + 1].add(B.offset)

            if A1.approximately(A2) or B1.approximately(B2):
                continue

            d = segment_distance(A1, A2, B1, B2, dir)
            if d is not None and (distance is None or d < distance):
                if not ignore_negative or d > 0 or approximately(d, 0):
                    distance = d

    return distance


def polygonProjectionDistance(A, B, direction):
    AP = A.points[:]
    BP = B.points[:]

    # Close the loop for polygons
    if AP[0] != AP[-1]:
        AP.append(AP[0])

    if BP[0] != BP[-1]:
        BP.append(BP[0])

    distance = None

    for i in range(len(BP)):
        # The shortest/most negative projection of B onto A
        min_projection = None

        for j in range(len(AP) - 1):
            p = BP[i].add(B.offset)
            s1 = AP[j].add(A.offset)
            s2 = AP[j + 1].add(A.offset)

            s12 = s2.sub(s1)
            if abs(s12.cross(direction)) < TOL:
                continue

            # Project point, ignore edge boundaries
            d = point_distance(p, s1, s2, direction)
            if d is not None and (min_projection is None or d < min_projection):
                min_projection = d

        if min_projection is not None and (distance is None or min_projection > distance):
            distance = min_projection

    return distance
def lineIntersect(A, B, E, F, infinite=False):
    a1 = B.y - A.y
    b1 = A.x - B.x
    c1 = B.x * A.y - A.x * B.y
    a2 = F.y - E.y
    b2 = E.x - F.x
    c2 = F.x * E.y - E.x * F.y

    denom = a1 * b2 - a2 * b1

    x = (b1 * c2 - b2 * c1) / denom
    y = (a2 * c1 - a1 * c2) / denom

    if not is_finite(x) or not is_finite(y):
        return None

    if not infinite:
        # Coincident points do not count as intersecting
        if abs(A.x - B.x) > TOL and ((A.x < B.x) and (x < A.x or x > B.x) or (A.x > B.x) and (x > A.x or x < B.x)):
            return None
        if abs(A.y - B.y) > TOL and ((A.y < B.y) and (y < A.y or y > B.y) or (A.y > B.y) and (y > A.y or y < B.y)):
            return None

        if abs(E.x - F.x) > TOL and ((E.x < F.x) and (x < E.x or x > F.x) or (E.x > F.x) and (x > E.x or x < F.x)):
            return None
        if abs(E.y - F.y) > TOL and ((E.y < F.y) and (y < E.y or y > F.y) or (E.y > F.y) and (y > E.y or y < F.y)):
            return None

    return Vector(x, y)
def intersect(A, B):
    AP = A.points[:]
    BP = B.points[:]

    for i in range(len(AP) - 1):
        for j in range(len(BP) - 1):
            a1 = AP[i].add(A.offset)
            a2 = AP[i + 1].add(A.offset)
            b1 = BP[j].add(B.offset)
            b2 = BP[j + 1].add(B.offset)

            prevbindex = len(BP) - 1 if j == 0 else j - 1
            prevaindex = len(AP) - 1 if i == 0 else i - 1
            nextbindex = 0 if j + 1 == len(BP) - 1 else j + 2
            nextaindex = 0 if i + 1 == len(AP) - 1 else i + 2

            # Adjust indices if we hit a loop endpoint
            if BP[prevbindex] == BP[j] or BP[prevbindex].approximately(BP[j]):
                prevbindex = len(BP) - 1 if prevbindex == 0 else prevbindex - 1

            if AP[prevaindex] == AP[i] or AP[prevaindex].approximately(AP[i]):
                prevaindex = len(AP) - 1 if prevaindex == 0 else prevaindex - 1

            # Adjust indices if we hit a loop endpoint
            if BP[nextbindex] == BP[j + 1] or BP[nextbindex].approximately(BP[j + 1]):
                nextbindex = 0 if nextbindex == len(BP) - 1 else nextbindex + 1

            if AP[nextaindex] == AP[i + 1] or AP[nextaindex].approximately(AP[i + 1]):
                nextaindex = 0 if nextaindex == len(AP) - 1 else nextaindex + 1

            a0 = AP[prevaindex].add(A.offset)
            b0 = BP[prevbindex].add(B.offset)

            a3 = AP[nextaindex].add(A.offset)
            b3 = BP[nextbindex].add(B.offset)

            if on_segment(a1, a2, b1) or a1.approximately(b1):
                b0in = point_in_polygon(b0, A)
                b2in = point_in_polygon(b2, A)
                if (b0in and not b2in) or (not b0in and b2in):
                    return True
                else:
                    continue

            if on_segment(a1, a2, b2) or a2.approximately(b2):
                b1in = point_in_polygon(b1, A)
                b3in = point_in_polygon(b3, A)
                if (b1in and not b3in) or (not b1in and b3in):
                    return True
                else:
                    continue

            if on_segment(b1, b2, a1) or a1.approximately(b2):
                a0in = point_in_polygon(a0, B)
                a2in = point_in_polygon(a2, B)
                if (a0in and not a2in) or (not a0in and a2in):
                    return True
                else:
                    continue

            if on_segment(b1, b2, a2) or a2.approximately(b1):
                a1in = point_in_polygon(a1, B)
                a3in = point_in_polygon(a3, B)
                if (a1in and not a3in) or (not a1in and a3in):
                    return True
                else:
                    continue

            p = line_intersect(b1, b2, a1, a2)

            if p is not None:
                return True

    return False
def searchStartPoint(A, B, inside, NFP):
    # Clone arrays
    AP = A.points[:]
    BP = B.points[:]

    # Close the loop for polygons
    if AP[0] != AP[-1]:
        AP.append(AP[0])

    if BP[0] != BP[-1]:
        BP.append(BP[0])

    for i in range(len(AP) - 1):
        if not AP[i].marked:
            AP[i].mark()

            for j in range(len(BP)):
                B.offset.set(AP[i].sub(BP[j]))

                Binside = None
                for k in range(len(BP)):
                    inpoly = point_in_polygon(BP[k].add(B.offset), A)
                    if inpoly is not None:
                        Binside = inpoly
                        break

                if Binside is None:  # A and B are the same
                    return None

                start_point = B.offset.clone()
                if ((Binside and inside) or (not Binside and not inside)) and not intersect(A, B) and not in_nfp(start_point, NFP):
                    return start_point

                # Slide B along vector
                v = AP[i + 1].sub(AP[i])

                d1 = polygon_projection_distance(A, B, v)
                d2 = polygon_projection_distance(B, A, v.negative())

                d = None

                # todo: clean this up
                if d1 is None and d2 is None:
                    pass  # nothing
                elif d1 is None:
                    d = d2
                elif d2 is None:
                    d = d1
                else:
                    d = min(d1, d2)

                # Only slide until no longer negative
                # todo: clean this up
                if d is not None and not approximately(d, 0) and d > 0:
                    pass
                else:
                    continue

                vd2 = v.squared_length()

                if d * d < vd2 and not approximately(d * d, vd2):
                    vd = vd2 ** 0.5
                    v = v.multiply_scalar(d / vd)

                B.offset.add(v)

                for k in range(len(BP)):
                    inpoly = point_in_polygon(BP[k].add(B.offset), A)
                    if inpoly is not None:
                        Binside = inpoly
                        break

                start_point = B.offset.clone()
                if ((Binside and inside) or (not Binside and not inside)) and not intersect(A, B) and not in_nfp(start_point, NFP):
                    return start_point

    # Returns None if no start point is found
    return None
def inNfp(p, nfp):
    if not nfp or len(nfp) == 0:
        return False

    for i in range(len(nfp)):
        for j in range(len(nfp[i].points)):
            if p.approximately(nfp[i].points[j]):
                return True

    return False


# Interior NFP for the case where A is a rectangle (Bin)
def noFitRectanglePolygon(A, B,*arg):
    #print(vars(A),vars(B))
    abb = A.bounds()
    bbb = B.bounds()
    

    # Returns None if B is larger than A
    if (bbb.max.x - bbb.min.x > abb.max.x - abb.min.x) or (bbb.max.y - bbb.min.y > abb.max.y - abb.min.y):
        return None

    p0 = Vector(abb.min.x - bbb.min.x, abb.min.y - bbb.min.y)
    p1 = Vector(abb.max.x - bbb.max.x, abb.min.y - bbb.min.y)
    p2 = Vector(abb.max.x - bbb.max.x, abb.max.y - bbb.max.y)
    p3 = Vector(abb.min.x - bbb.min.x, abb.max.y - bbb.max.y)

    return Polygon([
        B.points[0].add(p0),
        B.points[0].add(p1),
        B.points[0].add(p2),
        B.points[0].add(p3)
    ])
def noFitPolygon(A, B, inside=False, edges=False, debug=False):
    # Initialize all vertices and get reference to min y of A, max y of B
    minA = A.points[0].y
    minAindex = 0

    maxB = B.points[0].y
    maxBindex = 0

    la = len(A.points)
    lb = len(B.points)

    for i in range(1, la):
        A.points[i].unmark()
        if A.points[i].y < minA:
            minA = A.points[i].y
            minAindex = i

    for i in range(1, lb):
        B.points[i].unmark()
        if B.points[i].y > maxB:
            maxB = B.points[i].y
            maxBindex = i

    start_point = None

    if not inside:
        # Shift B such that the bottom-most point of B is at the top-most point of A
        start_point = A.points[minAindex].sub(B.points[maxBindex])
    else:
        # No reliable heuristic for inside
        start_point = search_start_point(A.clone(), B.clone(), True)

    result = []

    while start_point != None:
        B.offset.set(start_point)
        # Maintain a list of touching points/edges
        prev_vector = None  # Keep track of previous vector

        reference = B.points[0].add(B.offset)
        NFP = [reference.clone()]
        start = reference.clone()

        iterations = 0
        limit = 10 * (la + lb)

        while iterations < limit:
            iterations += 1

            touching = []

            # Find touching vertices/edges
            for i in range(la):
                next_i = 0 if i == la - 1 else i + 1
                for j in range(lb):
                    next_j = 0 if j == lb - 1 else j + 1
                    bj = B.points[j].add(B.offset)
                    if A.points[i].approximately(bj):
                        touching.append({'type': 0, 'A': i, 'B': j})
                    elif on_segment(A.points[i], A.points[next_i], bj):
                        touching.append({'type': 1, 'A': next_i, 'B': j})
                    elif on_segment(bj, B.points[next_j].add(B.offset), A.points[i]):
                        touching.append({'type': 2, 'A': i, 'B': next_j})

            # Generate translation vectors from touching vertices/edges
            vectors = []
            for t in touching:
                vertexA = A.points[t['A']]
                vertexA.mark()

                # Adjacent A vertices
                prevAindex = (t['A'] - 1) % la  # Loop
                nextAindex = (t['A'] + 1) % la  # Loop

                prevA = A.points[prevAindex]
                nextA = A.points[nextAindex]

                # Adjacent B vertices
                vertexB = B.points[t['B']]

                prevBindex = (t['B'] - 1) % lb  # Loop
                nextBindex = (t['B'] + 1) % lb  # Loop

                prevB = B.points[prevBindex]
                nextB = B.points[nextBindex]

                if t['type'] == 0:
                    va1 = prevA.sub(vertexA)
                    va2 = nextA.sub(vertexA)

                    vb1 = vertexB.sub(prevB)
                    vb2 = vertexB.sub(nextB)

                    vectors.append(IndexedVector(va1.x, va1.y, vertexA, prevA))
                    vectors.append(IndexedVector(va2.x, va2.y, vertexA, nextA))
                    vectors.append(IndexedVector(vb1.x, vb1.y, prevB, vertexB))
                    vectors.append(IndexedVector(vb2.x, vb2.y, nextB, vertexB))

                elif t['type'] == 1:
                    vb = vertexB.add(B.offset)
                    va1 = vertexA.sub(vb)
                    va2 = prevA.sub(vb)
                    vectors.append(IndexedVector(va1.x, va1.y, prevA, vertexA))
                    vectors.append(IndexedVector(va2.x, va2.y, vertexA, prevA))

                elif t['type'] == 2:
                    va1 = vertexA.sub(vertexB.add(B.offset))
                    va2 = vertexA.sub(prevB.add(B.offset))
                    vectors.append(IndexedVector(va1.x, va1.y, prevB, vertexB))
                    vectors.append(IndexedVector(va2.x, va2.y, vertexB, prevB))

            # Check vectors and reject immediate intersections
            translate = None
            maxd = 0

            for v in vectors:
                if v.x == 0 and v.y == 0:
                    continue

                # If this vector points us back to where we came from, ignore it
                if prev_vector and v.dot(prev_vector) < 0:
                    unit_vector = v.normalize()
                    prev_unit_vector = prev_vector.normalize()

                    if abs(unit_vector.cross(prev_unit_vector)) < 1e-8:
                        continue

                d = polygon_slide_distance(A, B, v, True)
                vecd2 = v.squared_length()
                if d is None or d * d > vecd2:
                    d = math.sqrt(vecd2)

                if d is not None and d > maxd:
                    maxd = d
                    translate = v

            if translate is None or approximately(maxd, 0):
                # Didn't close the loop, something went wrong
                NFP = None
                break

            translate.start.mark()
            translate.end.mark()

            # Trim
            vlength2 = translate.squared_length()
            maxd2 = maxd * maxd
            if maxd2 < vlength2 and not approximately(maxd2, vlength2):
                scale = math.sqrt(maxd2 / vlength2)
                translate = translate.multiply_scalar(scale)

            prev_vector = translate.clone()
            reference = reference.add(translate)

            if reference.approximately(start):
                break

            # Check if we looped
            looped = False
            if NFP:
                for p in NFP[:-1]:
                    if reference.approximately(p):
                        looped = True

            if looped:
                break

            NFP.append(reference.clone())
            B.offset = B.offset.add(translate)

        if NFP and len(NFP) > 0:
            result.append(Polygon(NFP))

        if not edges:
            # Only get outer NFP or first inner NFP
            break

        start_point = search_start_point(A.clone(), B.clone(), inside, result)

    return result
def minkowskiDifference(A, B):
    Ac = toClipperCoordinates(A.points)
    Bc = toClipperCoordinates(B.points)
    # Invert the points of B for Minkowski difference
    for i in range(len(Bc)):
        Bc[i]['X'] *= -1
        Bc[i]['Y'] *= -1
    Ac = [(i['X'], i['Y']) for i in Ac]
    Bc = [(i['X'], i['Y']) for i in Bc]
    solution = pyclipper.MinkowskiSum(Ac, Bc, True)
    #solution = [{'X': p[0], 'Y': p[1]} for p in solution[0]]
    #print(solution)
    min_area = float('inf')
    min_polygon = None
    for i in range(0,len(solution)):
        points = toNestCoordinates([{'X': p[0], 'Y': p[1]} for p in solution[i]])
        #print(points)
        polygon = Polygon(points)
        #print(vars(poly))
        area = polygon.area()
        if area < min_area:
            min_area = area
            min_polygon = polygon

    offset = B.points[0]
    return min_polygon.translate(offset.x, offset.y)


def offsetPolygon(polygon, offset, miter_limit=2.5, curve_tolerance=1.0):
    if approximately(offset, 0):
        return polygon

    clipper = ClipperLib.ClipperOffset(miter_limit, curve_tolerance * clipperScale)

    path = toClipperCoordinates(polygon.points)
    clipper.AddPath(path, ClipperLib.JoinType.jtSquare, ClipperLib.EndType.etClosedPolygon)

    paths = ClipperLib.Paths()
    clipper.Execute(paths, offset * clipperScale)

    # Keep polygon properties
    cloned = polygon.clone()

    points = toNestCoordinates(paths[0])
    cloned.points = points

    return cloned


def createUniqueKey(A, B, inside, *args):
    return json.dumps({
        "A": str(A),
        "B": str(B),
        "inside": inside
    })


# Define what will be available for import when using `from module_name import *`
__all__ = [
    "approximately",
    "bounds",
    "clipperScale",
    "clipperThreshold",
    "toClipperCoordinates",
    "toNestCoordinates",
    "noFitRectanglePolygon",
    "noFitPolygon",
    "minkowskiDifference",
    "offsetPolygon",
    "createUniqueKey"
]

