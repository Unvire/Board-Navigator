import math
import mathFunctions

class BoardObject():
    '''
    Parent class for board objects(holes, test points, components).
    '''
    COLLISION_TOLERANCE = 0.005
    def __init__(self, name=None, coords=None):
        '''
        Parent class. Attributes:
            self.name - name of the component
            self.coords - tuple of coords (x, y) or tuple of tuples of coords ((x1, y1), (x2, y2)...)
        '''
        self.name = name
        self.coords = coords

    def _movePoint(self, point, vector):
        '''
        Moves point by a vector
            point1 - tuple (x, y)
            point1 - tuple (x, y)
        '''
        x1, y1 = point
        x2, y2 = vector
        return x1 + x2, y1 + y2

class Component(BoardObject):
    def __init__(self, name=None, coords=None, side=None):
        '''
        Child class for BoardObject. Can be used to store holes data. Attributes:
            side - side of the component
            name, coords are explained in BoardObject class
        '''
        super().__init__(name, coords)
        self.side = side

    def checkCollision(self, checkCoords, scale):
        '''
        Checks if given coordinates are inside collision area and returns True or False based on checking. For Component instances it uses default area - enscribed square on circle (radius = 3 / baseScale).
            checkCoords - (x, y) coordinates to be checked
            scale - scaling factor of currently drawn layer
        '''
        checkX, checkY = checkCoords
        try:
            xRange, yRange = self.collisionArea
            return xRange[0] <= checkX <= xRange[1] and yRange[0] <= checkY <= yRange[1]

        except AttributeError:
            radius = 3 / scale
            for coords in self.coords:
                minX, minY = coords[0] - radius, coords[1] - radius
                xRange = minX, minX + 2 * radius
                yRange = minY, minY + 2 * radius

                if xRange[0] <= checkX <= xRange[1] and yRange[0] <= checkY <= yRange[1]:
                    return True
        return False

    def setCustomCaseScale(self, scale):
        '''
        Updates case dimension by multiplying each point by given scale and calls __init__ to update parameters
            scale - int or float
        '''
        x1, y1 = self.coords1
        x2, y2 = self.coords2

        scaledCoords1 = x1 * scale, y1 * scale
        scaledCoords2 = x2 * scale, y2 * scale
        self.__init__(self.name, self.coords, self.side, (self.caseName, self.caseShape, scaledCoords1, scaledCoords2))


class ComponentRectangle(Component):
    def __init__(self, name=None, coords=None, side=None, case=None, angle=0):
        '''
        Child class of Component. Can be used to stored component with rectangular shape. Attributes:
            case = (caseName, caseShape, (x1, y1), (x2, y2))
                caseName - string with case name
                caseShape - 'RECT' or 'CIRCLE'
                (x1, x2), (x2, y2) - coords of vertexes that are opposite on the same diagonal ((top, left), (botttom, right))
            angle - rotation angle of rectangle in degrees
            name, coords, side are explained in Component class

            self.points - list of points of the rectangle after rotation. Used to draw a polygon (rotated rectangle)
            self.collisionArea - tuple (minX, maxX), (minY, maxY). Used to detect collision with mouse click
        '''
        super().__init__(name, coords, side)
        self.angle = float(angle)
        #print(name, coords, side, case, angle)

        self.caseName, self.caseShape, self.coords1, self.coords2 = case

        x1, y1 = self.coords1
        x2, y2 = self.coords2

        self.point1 = self._movePoint(self.coords, mathFunctions.rotatePoint((x1, y1), self.angle))
        self.point2 = self._movePoint(self.coords, mathFunctions.rotatePoint((x2, y1), self.angle))
        self.point3 = self._movePoint(self.coords, mathFunctions.rotatePoint((x2, y2), self.angle))
        self.point4 = self._movePoint(self.coords, mathFunctions.rotatePoint((x1, y2), self.angle))
        self.points = [self.point1, self.point2, self.point3, self.point4]

        xCoordList = [point[0] for point in self.points]
        toleranceX = abs(min(xCoordList)) * BoardObject.COLLISION_TOLERANCE

        minX, maxX = min(xCoordList) - toleranceX , max(xCoordList) + toleranceX

        yCoordList =[point[1] for point in self.points]
        toleranceY = abs(min(yCoordList)) * BoardObject.COLLISION_TOLERANCE
        minY, maxY = min(yCoordList) - toleranceY, max(yCoordList) + toleranceY

        self.collisionArea = ((minX, maxX), (minY, maxY))

class ComponentCircle(Component):
    def __init__(self, name=None, coords=None, side=None, case=None, angle=0):
        '''
        Child class of Component. Can be used to stored component with circle shape. Attributes:
            case = (caseName, caseShape, (x1, y1), (x2, y2))
                caseName - string with case name
                caseShape - 'RECT' or 'CIRCLE'
                (x1, x2), (x2, y2) - coords of points that describe diameter
            angle - rotation angle (not used)
            name, coords, side are explained in Component class

            self.radius - radius of the circle
            self.collisionArea - tuple (minX, maxX), (minY, maxY). Used to detect collision with mouse click
        '''
        super().__init__(name, coords, side)

        self.caseName, self.caseShape, self.coords1, self.coords2 = case

        x1, y1 = self.coords1
        x2, y2 = self.coords2

        self.radius = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

        centerX, centerY = self.coords
        toleranceX = abs(centerX - self.radius) * BoardObject.COLLISION_TOLERANCE
        toleranceY = abs(centerY - self.radius) * BoardObject.COLLISION_TOLERANCE

        minX, minY = centerX - self.radius - toleranceX, (centerY - self.radius) - toleranceY
        width = height = 2 * self.radius
        maxX, maxY = (minX + width) + toleranceX, (minY + height) + toleranceX
        self.collisionArea = ((minX, maxX), (minY, maxY))


if __name__ == '__main__':
    a = ComponentRectangle('R1', (0, 0), 'B', ['AP_rect39.37x78.74', 'RECT', (0.079, 0.039), (0.039, 0.02)], 0)
    a.setCustomCaseScale(2)
    b = ComponentCircle('TP1', (5, 5), 'B', ['AP_rect39.37x78.74', 'CIRCLE', (0.025, 0.025), (0.05, 0.05)], 0)
    c = Component('Hole1', ((0, 0), (1, 1)))

    b.checkCollision((4.999, 4.999), 1)

