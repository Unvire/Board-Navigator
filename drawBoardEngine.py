import pygame
import schematicLoader
import math
import boardObjects
import mathFunctions

pygame.font.init()

class Board():
    WIDTH, HEIGHT = 1100, 750
    FPS = 60

    WHITE = 255, 255, 255
    YELLOW = 252, 186, 3
    YELLOW2 = 153, 115, 9
    BLUE = 21, 103, 235
    BLUE2 = 11, 70, 163
    RED = 210, 46, 46
    GREEN = 43, 194, 48
    GREEN2 = 46, 209, 138
    GREEN3 = 38, 84, 57
    BLACK = 0, 0, 0
    GRAY = 200, 200, 200
    GRAY2 = 100, 100, 100
    VIOLET = 171, 24, 149
    VIOLET2 = 107, 12, 93

    def __init__(self, components, nets, holes, boardOutlines, forceHoles=False, testPointPrefix='TP'):
        '''
        Creates Board instance. Arguments:
            components - dict of components (componentName: [(x, y), side, case]), where case is a list [caseName, caseShape, (x1, y1), (x2, y2)]
            nets - dict of nets (netName:{component:[pins]})
            holes - dict of holes (holeName: [(x1, y1), (x2, y2)...])
            boardOutlines - dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
            forceHoles - If true then holes have constant radius, if False radius of holes is scaled 1.15 * testpoint's radius
            testPointPrefix - Unique prefix that is common for all testpoints
        '''
        self.components = []
        self.testPoints = []
        self.nets = nets
        self.holes = [boardObjects.Component(key, holes[key]) for key in holes]
        self.boardOutlines = {key:boardOutlines[key] for key in boardOutlines if key not in ('AREA', 'ARC_MODE')}
        self.boardArea = boardOutlines['AREA']
        self.forceHoles = forceHoles
        self.testPointPrefix = testPointPrefix

        ## list of component instances
        for component in components:
            coords = components[component][0]
            side = components[component][1]
            angle = components[component][2]
            try:
                case = components[component][3]
            except IndexError:
                case = None, None, None, None

            if case[1] == 'RECT':
                newComponent = boardObjects.ComponentRectangle(component, coords, side, case, angle)
            elif case[1] == 'CIRCLE':
                newComponent = boardObjects.ComponentCircle(component, coords, side, case, angle)

            if component.startswith(self.testPointPrefix):
                self.testPoints.append(newComponent)
            else:
                self.components.append(newComponent)

        self.xMoveOffset = 0
        self.yMoveOffset = 0
        self.maxRelativeDistance = 200
        self.boxOutlineWidth, self.boxOutlineHeight = 200, 150
        self.rotationAngle = 0
        self.holeRadius = None

        ## calculate base scale and midpoint
        self.baseScale = self._calculateBaseScale()
        self.zoomScale = 1
        self.midPoint = self._calculateMidPoint()

        self.baseScale *= 0.8

        ## get x,y base offsets to draw board in the middle
        xList = [point[0] for point in self.boardArea]
        xMin, xMax = min(xList) * self.baseScale, max(xList) * self.baseScale
        xZeroOffset = -xMin
        self.xBaseOffset = (Board.WIDTH - (xMax - xMin)) // 2 + xZeroOffset

        yList = [point[1] for point in self.boardArea]
        yMin, yMax = min(yList) * self.baseScale, max(yList) * self.baseScale
        yZeroOffset = -yMin
        self.yBaseOffset = (Board.HEIGHT - (yMax - yMin)) // 2 + yZeroOffset
        #print(f'base offsets:({self.xBaseOffset}, {self.yBaseOffset}), base scale={self.baseScale}, board area:{self.boardArea}, recalculated board area:(x=({xMin}, {xMax}), y=({yMin}, {yMax}))')
        self.i = 0

    def _calculateBaseScale(self):
        '''
        Calculates base scale factor. Returns base scaling factor
            1. Calculate length of the board in both X axis and Y axis
            2. Calculate axis scale factor as Window/Surface dimension / length / sqrt(2) (sqrt(2) to fit image during rotation)
            3. Return smaller axis scale factor
        '''
        x1, x2 = [x for x, y in self.boardArea]
        y1, y2 = [y for x, y in self.boardArea]
        lengthX = abs(x1 - x2)
        lengthY = abs(y1 - y2)
        #scaleX = math.floor(Board.WIDTH / lengthX / math.sqrt(2))
        #scaleY = math.floor(Board.HEIGHT / lengthY / math.sqrt(2))
        scaleX = Board.WIDTH / lengthX / math.sqrt(2)
        scaleY = Board.HEIGHT / lengthY / math.sqrt(2)

        #print(scaleX, scaleY, '|', lengthX, lengthY, '|', x1, x2, '|', y1, y2)
        return min(scaleX, scaleY)

    def _calculateMidPoint(self):
        '''
        Calculates middle point of self.boardArea as midX = (x1 + x2) / 2), midY = ((y1 + y2) / 2)). Returns midpoint (midX, -midY)
        '''
        x1, x2 = [x for x, y in self.boardArea]
        y1, y2 = [y for x, y in self.boardArea]

        midX = (x1 + x2) / 2
        midY = (y1 + y2) / 2
        return midX, -midY

    def renderBoard(self, surface, side='B'):
        '''
        Rendes edges of the board into the surface
            Surface - pygame surface
            side - 'T' or 'B'
        '''
        invertX = side=='T'
        ## draw lines
        for point1, point2 in self.boardOutlines['LINES']:
            screenCoords1 = self.screenPoint(surface, point1, invertX)
            screenCoords2 = self.screenPoint(surface, point2, invertX)
            pygame.draw.line(surface, Board.WHITE, screenCoords1, screenCoords2)

        ## draw arcs
        for point1, point2, point3 in self.boardOutlines['ARCS']:
            screenCoords1 = self.screenPoint(surface, point1, invertX)
            screenCoords2 = self.screenPoint(surface, point2, invertX)
            screenCoords3 = self.screenPoint(surface, point3, invertX)

            rect, startAngle, endAngle = mathFunctions.threePointToPygameArc(screenCoords1, screenCoords2, screenCoords3)

            if invertX:
                startAngle, endAngle = endAngle, startAngle

            pygame.draw.arc(surface, Board.WHITE, rect, startAngle, endAngle)
            #pygame.draw.circle(surface, Board.RED, screenCoords1, 3); pygame.draw.circle(surface, Board.BLUE, screenCoords2, 3); pygame.draw.circle(surface, Board.GREEN2, screenCoords3, 3)
            #print(screenCoords1, screenCoords2, screenCoords3, startAngle*180/math.pi, endAngle*180/math.pi)

    def renderTestPoints(self, surface, side='B'):
        '''
        Renders test points of the board into the surface
            Surface - pygame surface
            side - 'T' or 'B'
        '''
        invertX = side=='T'
        for testPoint in self.testPoints:
            if testPoint.side == side:
                x, y = testPoint.coords

                ## draw proper shape
                if testPoint.caseShape == 'RECT':
                    screenPoints = [self.screenPoint(surface, point, invertX) for point in testPoint.points]
                    pygame.draw.polygon(surface, Board.YELLOW, screenPoints)
                    pygame.draw.polygon(surface, Board.YELLOW2, screenPoints, width=1)
                elif testPoint.caseShape == 'CIRCLE':
                    center = self.screenPoint(surface, (x, y), invertX)
                    radius = testPoint.radius * self.baseScale * self.zoomScale
                    pygame.draw.circle(surface, Board.YELLOW, center, radius)
                    pygame.draw.circle(surface, Board.YELLOW2, center, radius, width=1)
                    if not self.forceHoles:
                        self.holeRadius = 1.15 * radius

    def renderComponents(self, surface, side='B'):
        '''
        Rendes components of the board into the surface
            Surface - pygame surface
            side - 'T' or 'B'
        '''
        invertX = side=='T'
        for component in self.components:
            if component.side == side:
                x, y = component.coords

                ## draw proper shape
                if component.caseShape == 'RECT':
                    screenPoints = [self.screenPoint(surface, point, invertX) for point in component.points]
                    pygame.draw.polygon(surface, Board.GREEN2, screenPoints)
                    pygame.draw.polygon(surface, Board.GREEN3, screenPoints, width=1)
                elif component.caseShape == 'CIRCLE':
                    center = self.screenPoint(surface, (x, y), invertX)
                    radius = component.radius * self.baseScale * self.zoomScale
                    pygame.draw.circle(surface, Board.GREEN2, center, radius)
                    pygame.draw.circle(surface, Board.GREEN3, center, radius, width=1)

    def renderHoles(self, surface, side='B'):
        '''
        Rendes holes of the board into the surface.
            Surface - pygame surface
            side - 'T' or 'B'
        '''
        invertX = side=='T'
        for hole in self.holes:
            for coords in hole.coords:
                x, y = coords
                if not self.forceHoles and self.holeRadius:
                    radius = self.holeRadius
                else:
                    radius = 4 * self.zoomScale
                screenCoords = self.screenPoint(surface, (x, y), invertX)
                pygame.draw.circle(surface, Board.BLUE, screenCoords, radius)
                pygame.draw.circle(surface, Board.BLUE2, screenCoords, radius, width=1)

    def screenPoint(self, surface, coords, invertX=False):
        '''
        Calculates point's coordinates related to screen. Returns recalculated tuple (screenX, screenY)
            surface - surface on which the point will be rendered
            coords - tuple (x, y) to calculated into screen coords
            invertX = True/False - mirrors X axis
        '''
        pointX, pointY = coords

        ## translation
        pointXMoved = pointX * self.baseScale + self.xBaseOffset
        pointYMoved = pointY * self.baseScale + self.yBaseOffset

        midPointMoved = self.translateMidPoint()

        ## rotation
        if invertX:
            pointXRotated, pointYRotated = mathFunctions.rotatePoint((pointXMoved, pointYMoved), -self.rotationAngle, rotationPoint=midPointMoved)
        else:
            pointXRotated, pointYRotated = mathFunctions.rotatePoint((pointXMoved, pointYMoved), self.rotationAngle, rotationPoint=midPointMoved)

        ## scaling
        screenPointX = pointXRotated * self.zoomScale
        screenPointY = pointYRotated * self.zoomScale

        if invertX:
            screenPointX = surface.get_width() - screenPointX

        return screenPointX, screenPointY

    def inverseScreenPoint(self, surface, screenCoords, invertX=False):
        '''
        Inverse function for screenPoint. Converts screen coords to layer coords. Returns recalculated tuple (pointX, pointY)
            surface - surface that screenCoords are related to
            coords - tuple (x, y) to calculated into surface coords
            invertX = True/False - mirrors X axis
        '''
        screenPointX, screenPointY = screenCoords
        ## reverse move vector and zoom scale
        if invertX:
            screenPointX = surface.get_width() - screenPointX
            pointX = (screenPointX + self.xMoveOffset) / self.zoomScale
            angle = self.rotationAngle
        else:
            pointX = (screenPointX - self.xMoveOffset) / self.zoomScale
            angle = -self.rotationAngle
        pointY = (screenPointY - self.yMoveOffset) / self.zoomScale

        ## reverse rotation
        midPointMoved = self.translateMidPoint()
        pointX, pointY = mathFunctions.rotatePoint((pointX, pointY), angle, rotationPoint=midPointMoved)

        ## reverse base translation and base scale
        pointX = (pointX - self.xBaseOffset) / self.baseScale
        pointY = (pointY - self.yBaseOffset) / self.baseScale

        return pointX, pointY

    def translateMidPoint(self):
        '''
        Returns midpoint of the board in the screen coordinates. Returns (x, y) sequence
        '''
        midX, midY = self.midPoint

        midXMoved = midX * self.baseScale + self.xBaseOffset
        midYMoved = -midY * self.baseScale + self.yBaseOffset #-y because yAxis is facing down in pygame
        return midXMoved, midYMoved

    def renderMarker(self, surface, coords):
        '''
        Draws an arrow marker. Base point is in the tip.
            surface - pygame surface
            coords - tuple of (x, y) coords
        '''
        x, y = coords
        point1 = x, y - 2
        point2 = x - 7, y - 20
        point3 = x - 3, y - 20
        point4 = x - 3, y - 70
        point5 = x + 3, y - 70
        point6 = x + 3, y - 20
        point7 = x + 7, y - 20
        points = point1, point2, point3, point4, point5, point6, point7
        pygame.draw.polygon(surface, Board.RED, points)

    def renderBoardLayer(self, boardLayer, side, marker, netComponents):
        '''
        Renders on surface board outline, components, holes and marker. (board ooutline -> Holes -> netComponents -> testpoints -> marker)
            boardLayer - pygame surface
            side - side of the board ('T' or 'B')
            marker = (renderMarker, coords) - tuple of True/False(should marker be rendered?) and coords of marker (coords of where to render marker)
            netComponents = sequence of ((x, y), side) (x, y are coords from file to be recalculated into the screenPoint)
        '''
        isMarker, markerCoords = marker


        self.renderBoard(boardLayer, side)
        self.renderHoles(boardLayer, side)
        if netComponents:
            self.renderNetComponents(boardLayer, side, netComponents)
        self.renderTestPoints(boardLayer, side)
        self.renderComponents(boardLayer, side)
        if isMarker:
            self.renderMarker(boardLayer, markerCoords)

    def createLayers(self):
        '''
        Returns boardLayer (surface on which pcba is drawn) and mouseLayer (surface on which cursor outline is drawn)
        '''
        self.boardLayer = pygame.Surface((Board.WIDTH * self.zoomScale,
                                     Board.HEIGHT * self.zoomScale))
        self.mouseLayer = pygame.Surface((Board.WIDTH, Board.HEIGHT))
        self.mouseLayer.set_colorkey((Board.BLACK)) # set black as transparent

    def updateLayers(self, boardLayerData, mouseLayerData, netComponents=[]):
        '''
        Updates layers - draws marker on board layer, cursor outline on mouse layer, and marks component on selected net
            boardLayerData = side, ('T' or 'B')
                             markerData (True/False, (x,y))
            mouseLayerData = cursorCoords, (x, y)
                             cursorColor (R, G, B)
            netComponents = sequence of ((x, y), side)
        '''
        side, markerData = boardLayerData
        self.renderBoardLayer(self.boardLayer, side, markerData, netComponents)

        cursorCoords, cursorColor = mouseLayerData
        if cursorCoords:
            self.renderCursorOutline(self.mouseLayer, cursorCoords, cursorColor)

    def renderImage(self, targetSurface):
        '''
        Prepares image by bliting board layer and mouseLayer into target surface
            targetSurface - surface with final image
        '''
        targetSurface.fill(Board.BLACK)
        targetSurface.blit(self.boardLayer, (self.xMoveOffset, self.yMoveOffset))
        targetSurface.blit(self.mouseLayer, (0, 0))

    def renderCursorOutline(self, layer, coords, color):
        '''
        Renders rectangle outline around the cursor.
            layer - pygame surface
        '''
        x, y = coords
        pygame.draw.rect(layer, color, (x - self.boxOutlineWidth // 2, y - self.boxOutlineHeight // 2, self.boxOutlineWidth, self.boxOutlineHeight), 3)

    def renderNetComponents(self, surface, side, netComponents):
        '''
        Renders circular outline around each of the passed netComponents. Radius = 10 * self.zoomScale
            surface - pygame surface with components
            side - currently drawn side
            netComponents - sequence of ((x, y), side), where (x, y) defines coordinates of component in component coordinate system (coords in schematic file)
        '''
        componentsOnSide = [componentCoords for componentCoords, componentSide in netComponents if componentSide == side]
        for componentCoords in componentsOnSide:
            invertX = side == 'T'
            center = self.screenPoint(self.boardLayer, componentCoords, invertX)
            pygame.draw.circle(surface, Board.VIOLET, center, 10 * self.zoomScale, width=3)
            pygame.draw.circle(surface, Board.VIOLET2, center, 10 * self.zoomScale - 3, width=1)
            pygame.draw.circle(surface, Board.VIOLET2, center, 10 * self.zoomScale, width=1)

    def getSetMoveVector(self, deltaVector, forceChange=False):
        '''
        Updates xMoveOffset and yMoveOffset, if absolute relative value is smaller than self.maxRelativeDistance. Returns updated value of xMoveOffset and yMoveOffset.
            deltaVector - tuple of (deltaX, deltaY)
            forceChange - bool value that bypasses the maxRelativeDistance limit
        '''
        x, y = deltaVector
        if abs(x) < self.maxRelativeDistance or forceChange:
            self.xMoveOffset += x
        if abs(y) < self.maxRelativeDistance or forceChange:
            self.yMoveOffset += y
        return self.xMoveOffset, self.yMoveOffset

    def zoom(self, coords, sign='+'):
        '''
        Handles zooming of the board layer surface by changing self.zoomScale and moveVector so that board does not run away when zoomed. Returns deltaVector (deltaX, deltaY) that should be passed to getSetMoveVector method
            sign = '+' or '-'
            coords - (x, y)
        '''
        x, y = coords
        deltaX, deltaY = 0, 0
        if sign == '+':
            if self.zoomScale + 0.2 < 5:
                self.zoomScale += 0.2
                deltaX = -(x * 0.2)
                deltaY = -(y * 0.2)
        elif sign == '-':
            if self.zoomScale - 0.2 > .5:
                self.zoomScale -= 0.2
                deltaX = (x * 0.2)
                deltaY = (y * 0.2)

        return deltaX, deltaY

    def findComponentUsingName(self, surface, componentName):
        '''
        Iterates over self.testPoints + self.components + self.holes. If component exists then it returns its screen coords and side for setting up a marker. If there is no such component
        then (None, None), None is returned
            surface - surface on which components are drawn
            componentName - name of component
        '''

        searchList = self.testPoints + self.components + self.holes

        for component in searchList:
            if component.name == componentName:
                invertX = component.side == 'T'
                coords = component.coords
                if not isinstance(coords[0], float):
                    continue
                screenX, screenY = self.screenPoint(surface, coords, invertX)
                return (float(screenX), float(screenY)), component.side
        return (None, None), None

    def findComponentUsingClick(self, surface, screenCoords, side):
        '''
        Iterates over self.testPoints + self.components + self.holes. If given coords collide with any of the collision area of the component it returns its name.
        If no component is found then None is returned.
            surface - surface on which components are drawn
            screenCoords - absolute coordinates of cursor
            side - currently drawn side of pcba
        '''
        invertX = side=='T'
        pointX, pointY = self.inverseScreenPoint(surface, screenCoords, invertX)
        #print(screenCoords, pointX, pointY, f'offsets:{self.xBaseOffset}+{self.xMoveOffset}, scale:{self.baseScale}')

        searchList = self.holes + self.testPoints + self.components # holes are searched first because TH has priority
        for component in searchList:
            if component.side in (side, None): # check if component is on the currently drawn side or it is a hole (boardObjects.Component has default side=None)
                if component.checkCollision((pointX, pointY), self.baseScale * self.zoomScale):
                    isHole = not component.side
                    return component.name, isHole

        return None, None

    def defaultView(self):
        '''
        Sets default view by reseting move offsets and zoom coefficient
        '''
        self.xMoveOffset = 0
        self.yMoveOffset = 0
        self.zoomScale = 1
        self.rotationAngle = 0

    def setRotationAngle(self, angleDeg):
        '''
        Setter for self.rotationAngle
        '''
        self.rotationAngle = angleDeg

    def setComponentsCustomScale(self, scale):
        '''
        Updates case dimension by multiplying each point by given scale and calls __init__ to update parameters
            scale - int or float
        '''
        for component in (self.components + self.testPoints):
            component.setCustomCaseScale(scale)

#### camcad and gencad
'''
if __name__ == '__main__':
    ## pygame
    WIN = pygame.display.set_mode((Board.WIDTH, Board.HEIGHT))
    clock = pygame.time.Clock()

    run = True
    move = False
    isMouseRelPosCalledFirst = False
    moveVector = 0, 0
    coords = 0,0

    ## 5V
    net = [((-0.6095276, 3.040157), 'T'), ((-0.499685, 3.032756), 'T'), ((-0.699685, 2.902756), 'T'), ((-0.699685, 3.012756), 'T'), ((-0.555, 2.6), 'T'), ((-0.53, 2.85), 'T'), ((-0.419685, 3.032756), 'T'), ((-0.43, 3.0), 'B')]

    ## load components data cad file (camcad's .cad or gencad's .gcd)
    components, nets, holes, boardOutlines, _, _ = schematicLoader.SchematicLoader.loadSchematic('nexyM.gcd')
    board = Board(components, nets, holes, boardOutlines, 'TP')
    board.setComponentsCustomScale(1)

    ## set drawn side
    sideQueue = ['B', 'T']
    side = sideQueue[1]

    while run:
        clock.tick(Board.FPS)

        ## handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                ## moving layer
                pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
                move = True

                ## finding name of clicked component
                mouseCoords = pygame.mouse.get_pos()
                clickedComponent, isHole = board.findComponentUsingClick(board.boardLayer, mouseCoords, side)
                coords = board.inverseScreenPoint(board.boardLayer, mouseCoords)
                coords = board.screenPoint(board.boardLayer, coords)
                if clickedComponent:
                    print(clickedComponent, isHole)

            elif event.type == pygame.MOUSEBUTTONUP:
                ## moving layer
                move = False
                pygame.mouse.set_cursor(pygame.cursors.Cursor())
                isMouseRelPosCalledFirst = True
            elif event.type == pygame.KEYDOWN:
                ## zooming
                if event.key == pygame.K_PAGEUP:
                    deltaVector = board.zoom(coords, '+')
                    moveVector = board.getSetMoveVector(deltaVector)
                elif event.key == pygame.K_PAGEDOWN:
                    deltaVector = board.zoom(coords, '-')
                    moveVector = board.getSetMoveVector(deltaVector)
                elif event.key == pygame.K_SEMICOLON:
                    ## switch sides with "shift register" cycle
                    sideQueue.append(sideQueue.pop(0))
                    side = sideQueue[0]

        ## handle movement
        if move and isMouseRelPosCalledFirst:
            pygame.mouse.get_rel()
            isMouseRelPosCalledFirst = False
        elif move:
            currentPosRel = pygame.mouse.get_rel()
            moveVector = board.getSetMoveVector(currentPosRel)

        ## 1. create surfaces with PCB
        board.createLayers()

        ## 2. update marker coords
        markerCoords, markerSide = board.findComponentUsingName(board.boardLayer, 'TP617')
        if markerSide != side:
            markerSide = None
        markerData = markerSide, markerCoords

        angle = 0
        board.setRotationAngle(angle)

        ## 3. update created surfaces
        board.updateLayers((side, markerData), (pygame.mouse.get_pos(),  Board.GRAY), net)

        ## rotation test
        pygame.draw.circle(board.boardLayer, Board.RED, board.screenPoint(board.boardLayer, board.midPoint), 10)
        pygame.draw.circle(board.boardLayer, Board.BLUE, coords, 10)

        ## 4. put everything on one surface
        board.renderImage(WIN)

        ## display image
        pygame.display.update()
        #run = False

    pygame.quit()
'''

### odb++
if __name__ == '__main__':
    ## pygame
    WIN = pygame.display.set_mode((Board.WIDTH, Board.HEIGHT))
    clock = pygame.time.Clock()

    run = True
    move = False
    isMouseRelPosCalledFirst = False
    moveVector = 0, 0
    coords = 0,0

    ## load components data cad file (tgz)
    components, nets, holes, boardOutlines, _, _ = schematicLoader.SchematicLoader.loadSchematic('odb_15020617_01.tgz')
    board = Board(components, nets, holes, boardOutlines, 'TP')
    board.setComponentsCustomScale(40)

    ## set drawn side
    sideQueue = ['B', 'T']
    side = sideQueue[1]

    #board.holes = []
    for component in board.components:
        if component.name == 'DZ1':
            print(component.name, component.coords)

    while run:
        clock.tick(Board.FPS)

        ## handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                ## moving layer
                pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
                move = True

                ## finding name of clicked component
                mouseCoords = pygame.mouse.get_pos()
                clickedComponent, isHole = board.findComponentUsingClick(board.boardLayer, mouseCoords, side)
                coords = board.inverseScreenPoint(board.boardLayer, mouseCoords)
                coords = board.screenPoint(board.boardLayer, coords)
                if clickedComponent:
                    print(clickedComponent, isHole)

            elif event.type == pygame.MOUSEBUTTONUP:
                ## moving layer
                move = False
                pygame.mouse.set_cursor(pygame.cursors.Cursor())
                isMouseRelPosCalledFirst = True
            elif event.type == pygame.KEYDOWN:
                ## zooming
                if event.key == pygame.K_PAGEUP:
                    deltaVector = board.zoom(coords, '+')
                    moveVector = board.getSetMoveVector(deltaVector)
                elif event.key == pygame.K_PAGEDOWN:
                    deltaVector = board.zoom(coords, '-')
                    moveVector = board.getSetMoveVector(deltaVector)
                elif event.key == pygame.K_SEMICOLON:
                    ## switch sides with "shift register" cycle
                    sideQueue.append(sideQueue.pop(0))
                    side = sideQueue[0]

        ## handle movement
        if move and isMouseRelPosCalledFirst:
            pygame.mouse.get_rel()
            isMouseRelPosCalledFirst = False
        elif move:
            currentPosRel = pygame.mouse.get_rel()
            moveVector = board.getSetMoveVector(currentPosRel)

        ## 1. create surfaces with PCB
        board.createLayers()

        ## 2. update marker coords
        markerCoords, markerSide = board.findComponentUsingName(board.boardLayer, 'TP617')
        if markerSide != side:
            markerSide = None
        markerData = markerSide, markerCoords

        angle = 0
        board.setRotationAngle(angle)

        ## 3. update created surfaces
        board.updateLayers((side, markerData), (pygame.mouse.get_pos(),  Board.GRAY), [])

        ## 4. put everything on one surface
        board.renderImage(WIN)

        ## display image
        pygame.display.update()
        #run = False

    pygame.quit()