import math

def threePointToPygameArc(point1, point2, point3):
    '''
    Converts arc given as startPoint, endPoint, cirlceCenterPoint to pygame arc (rect, startAngle, endAngle)
    '''
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    radius = ((x1 - x3)**2 + (y1 - y3)**2) ** 0.5
    rect = (x3 - radius, y3 - radius, 2 * radius, 2 * radius) # top, left, width, height -> pygame rect

    x1Moved, y1Moved = (x1 - x3), -(y1 - y3) # x and y must be calculated related to the 0,0 point
    anglePoint1 = quadrantAngle(x1Moved, y1Moved)

    x2Moved, y2Moved = (x2 - x3), -(y2 - y3)
    anglePoint2 = quadrantAngle(x2Moved, y2Moved)

    return rect, anglePoint2, anglePoint1

def getQuadrant(x, y):
    '''
    Returns quadrant of carthesian coordinates system that point (x, y) belongs to or 0 if point is on OX or OY axis.
        X, y - coordinates
    '''
    if y > 0:
        if x > 0:
            return 1
        elif x < 0:
            return 2
        else:
            return 0
    elif y < 0:
        if x > 0:
            return 4
        elif x < 0:
            return 3
        else:
            return 0
    return 0

def quadrantAngle(x, y):
    '''
    Returns angle between OX axis and line going through x,y point. Value range: 0, 2*pi
        x, y - point coordinates
    '''
    quadrant = getQuadrant(x, y)
    angleRad = math.atan2(y, x)

    if quadrant in (1, 2):
        return angleRad
    elif quadrant in (3, 4):
        return 2 * math.pi + angleRad
    else:
        return angleRad if angleRad >= 0 else 2 * math.pi + angleRad

def rotatePoint(point, angleDeg, rotationPoint=(0, 0)):
    '''
    Rotates given point (x, y) around the (0, 0) point by given angle and returns (xRotated, yRotated)
        point - (x, y) tuple
        angleDeg - rotation angle in degrees
    '''
    x, y = point
    midX, midY = rotationPoint

    ## translate related to the rotation point
    x -= midX
    y -= midY

    ## rotate
    angleRad = math.radians(angleDeg)
    xRotated = x * math.cos(angleRad) - y * math.sin(angleRad)
    yRotated = x * math.sin(angleRad) + y * math.cos(angleRad)

    ## undo translation
    xRotated += midX
    yRotated += midY
    return xRotated, yRotated

def translate2D(point, vector):
    '''
    Translates point by a vactor. Returns (xMoved, yMoved)
        point = (x, y)
        vector = (u, v)
    '''
    x, y = point
    u, v = vector
    return x + u, y + v

if __name__ == '__main__':
    print(getQuadrant(1, 1))
    print(quadrantAngle(1, -1) * 180/math.pi)
    print(rotatePoint((1,1), 90))