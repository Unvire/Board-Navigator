import os
import mathFunctions
import math

class GenCADLoader():
    ## default values for shapes
    CIRCLE_DIMENSIONS = [(0.050, 0.050), (0.025, 0.025)]
    RECTANGLE_DIMENSIONS = [(-0.020, -0.016), (0.020, 0.016)]

    def __init__(self):
        '''
        Creates GenCADLoader instance. Attributes:
            self.sections - dict of sections in file (sectionName:[sectionStart, sectionEnd], where sectionStart, sectionEnd are line's numbers)
            self.schematic  - list of lines in .cad file
            self.components - dict of components (componentName: [(x, y), side, case])
            self.holes - dict of TH holes (componentName: [(x, y), ...])
            self.nets - dict of nets (netName:{component:[pins]})
            self.boardOutlines -  dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
            self.shapes - dict of shapes
        '''
        self.sections = {'BOARD':[],
                         'PADS':[],
                         'PADSTACKS':[],
                         'SHAPES':[],
                         'COMPONENTS':[],
                         'SIGNALS':[],
                         'MECH':[],
                         'TESTPINS':[]}
        self.schematic = []
        self.components ={}
        self.holes ={}
        self.nets = {}
        self.boardOutlines = {'AREA':[], 'LINES':[], 'ARCS':[]}
        self.shapes = {}

    def loadSchematic(self, name, path='Schematic'):
        '''
        Opens a .gcd file and returns dict of components, dict of nets, dict of holes and list of board vertexes. For manual processig of file use
        (openFile, getShapes, getComponents, getHoles, getBoardOutlines methods)
        '''
        self.openFile(name, path)

        nets = self.getNets()
        shapes = self.getShapes()
        components = self.getComponents()
        holes = self.getHoles()
        boardOutlines = self.getBoardOutlines()

        return components, nets, holes, boardOutlines, None, None


    def openFile(self, name, path='Schematic'):
        '''
        Opens a .gcd file and creates a dict of sections (sectionName:[sectionStart, sectionEnd], where sectionStart, sectionEnd are line's numbers)
        '''
        filePath = os.path.join(os.getcwd(), path, name)

        with open(filePath, 'r') as file:
            for i, line in enumerate(file):
                line = line.replace('\n', '').replace('  ',' ')
                if line[1:] in self.sections or line[4:] in self.sections:
                    key = line[1:].replace('END', '')
                    self.sections[key].append(i)
                self.schematic.append(line)

    def getBoardOutlines(self):
        '''
        Gets components from self.schematic. Iterates over BOARDOUTLINE Section.
        Returns dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        ## closest and furthest point from 0,0
        maxX, minX = float('-Inf'), float('Inf')
        maxY, minY = float('-Inf'), float('Inf')

        for i in self._getRange('BOARD'):
            line = self.schematic[i].split(' ')
            shape = line[0]
            if shape == 'LINE':
                point1 = float(line[1]), float(line[2])
                point2 = float(line[3]), float(line[4])
                self.boardOutlines['LINES'].append([point1, point2])

                minX = min([minX, point1[0], point2[0]])
                maxX = max([maxX, point1[0], point2[0]])
                minY = min([minY, point1[1], point2[1]])
                maxY = max([maxY, point1[1], point2[1]])

            elif shape == 'ARC':
                point1 = float(line[1]), float(line[2])
                point2 = float(line[3]), float(line[4])
                point3 = float(line[5]), float(line[6])
                self.boardOutlines['ARCS'].append([point1, point2, point3])
            
            if shape == 'ARTWORK': # artwork -> data about printed lines on pcb, not needed for this project
                break

        self.boardOutlines['AREA'] = [(minX, minY), (maxX, maxY)]
        return self.boardOutlines

    def getShapes(self):
        '''
        Gets shapes from self.schematic. Iterates over SHAPES section and returns dict {shapeName, shapeType, shapeCoords1, shapeCoords2}.
        Shape coords are assigned as a class constants and not read from file. BY default all shapes are classified as RECT. Testpoints are then changed to CIRCLE
        '''
        i = self.sections['SHAPES'][0] + 1
        iEnd = self.sections['SHAPES'][1]

        while i < iEnd:
            while 'SHAPE' not in self.schematic[i]:
                i += 1
            line = self.schematic[i].split(' ')
            try:
                shapeName = line[1]
                shapeType = 'RECT'
                shapeCoords = GenCADLoader.RECTANGLE_DIMENSIONS
                self.shapes[shapeName] = [shapeName, shapeType] + shapeCoords        
            except IndexError:
                pass
            i += 1
        
        return self.shapes

    def getComponents(self, testPointChars='TP'):
        '''
        Gets components from self.schematic. Iterates over Components Section and adds matching componentCase
        Returns dict of components (componentName: [(x, y), side, case]). Arguments:
            testPointChars - string based on which testpoints are recognized
        '''
        i = self.sections['COMPONENTS'][0] + 1
        iEnd = self.sections['COMPONENTS'][1]

        while i < iEnd:
            firstWord = self.schematic[i].split(' ')[0]
            if 'COMPONENT' == firstWord:
                componentName = self.schematic[i].split(' ')[1]
                i += 1
                ## 4 parameters must be read. Order can be random. This solution stores them in dict and gets data from it later
                readParameters = 0
                componentData = {'PLACE':None, 'LAYER':None, 'ROTATION':None, 'SHAPE':None}
                while readParameters != 4:
                    buffer = self.schematic[i].split(' ')
                    if buffer[0] in componentData:
                        componentData[buffer[0]] = buffer[1:]
                        readParameters += 1
                    i += 1
                componentCoords = componentData['PLACE']
                componentCoords = tuple([float(coord) for coord in componentCoords])
                componentSide = componentData['LAYER'][0][0] # first letter
                componentAngle = componentData['ROTATION'][0]
                componentCase = componentData['SHAPE'][0]

                ## replace testpoints with circles
                self.components[componentName] = [componentCoords, componentSide, componentAngle, self.shapes[componentCase]]
                if testPointChars in componentName:
                    self.components[componentName][3][1] = 'CIRCLE'
                    self.components[componentName][3][2], self.components[componentName][3][3] = GenCADLoader.CIRCLE_DIMENSIONS
            else:
                i += 1

        return self.components

    def getNets(self):
        '''
        Gets components from self.schematic. Iterates over SIGNAL Section.
        Returns dict of nets (netName:{component:[pins]})
        '''
        i = self.sections['SIGNALS'][0] + 1
        iEnd = self.sections['SIGNALS'][1]

        while i < iEnd:
            line = self.schematic[i].split(' ')
            if 'SIGNAL' in line:
                netName = line[1]
                self.nets[netName] = {}
            elif 'NODE' in line:
                componentName = line[1]
                componentPin = line[2]
                if not componentName in self.nets[netName]:
                    self.nets[netName][componentName] = [componentPin]
                else:
                    self.nets[netName][componentName].append(componentPin)

            i += 1

        return self.nets

    def getHoles(self):
        '''
        Gets holes from self.schematic. Iterates over SHAPES (pin -> component) and MECH Section.
        Returns dict of holes (holeName: [(x1, y1), (x2, y2)...])
        '''
        ## get every pin of shape if in shape there is INSERT thmt line
        i = self.sections['SHAPES'][0] + 1
        iEnd = self.sections['SHAPES'][1]

        shapeHoles = {}
        mountType = None
        holesCoords = []
        THTMarking = ['thmt']
        while i < iEnd:
            buffer = self.schematic[i].split(' ')           
            if buffer[0] == 'SHAPE':
                if mountType in THTMarking:
                    shapeHoles[shapeName] = holesCoords
                
                holesCoords = []
                shapeName = buffer[1]
            elif buffer[0] == 'INSERT':
                mountType = buffer[1]
            elif buffer[0] == 'PIN':
                holesCoords.append(tuple([float(buffer[3]), float(buffer[4])]))
            
            i += 1

        ## match shape with component names
        i = self.sections['COMPONENTS'][0] + 1
        iEnd = self.sections['COMPONENTS'][1]
        for component in self.components:
            componentCase = self.components[component][3][0]
            if componentCase in shapeHoles:
                componentCoords = self.components[component][0]
                xComponent, yComponent = [float(coord) for coord in componentCoords]
                componentAngle = float(self.components[component][2])
                
                for hole in shapeHoles[componentCase]:
                    ## rotate point by given angle
                    xHole, yHole = hole
                    xRotated, yRotated = mathFunctions.rotatePoint((xHole, yHole), componentAngle)

                    ## movethe coords
                    resultCoords = xComponent + xRotated, yComponent + yRotated
                    if component not in self.holes:
                        self.holes[component] = []
                    self.holes[component].append(resultCoords)
        '''
        while i < iEnd:
            componentName = self.schematic[i].split(' ')[1]
            componentCoords = self.schematic[i + 2].split(' ')[1:]
            xComponent, yComponent = [float(coord) for coord in componentCoords]
            componentAngle = float(self.schematic[i + 4].split(' ')[1])
            componentCase = self.schematic[i + 5].split(' ')[1]

            if componentCase in shapeHoles:
                self.holes[componentName] = []
                for hole in shapeHoles[componentCase]:
                    ## rotate point by given angle
                    xHole, yHole = hole
                    xRotated, yRotated = mathFunctions.rotatePoint((xHole, yHole), componentAngle)

                    resultCoords = xComponent + xRotated, yComponent + yRotated
                    self.holes[componentName].append(resultCoords)
            i += 6
        '''

        ## add mechanical holes
        i = self.sections['MECH'][0] + 1
        iEnd = self.sections['MECH'][1]

        while i < iEnd:
            line = self.schematic[i].split(' ')
            if 'HOLE' in line[0]:
                holeName = line[0]
                holeCoords = float(line[1]), float(line[2])
            else:
                holeName = line[1]
                try:
                    holeCoords = float(line[-6]), float(line[-5])
                except IndexError:
                    i += 1
                    continue
            self.holes[holeName] = [holeCoords]
            i += 1

        return self.holes

    def _getRange(self, sectionName):
        '''
        Helper method for getting range of a section. Returns range
        '''
        rangeStart = self.sections[sectionName][0]
        rangeEnd = self.sections[sectionName][1]

        return range(rangeStart, rangeEnd)

if __name__ == '__main__':
    a = GenCADLoader()
    #a.openFile('nexyM.gcd')
    a.openFile('wallbox som.gcd')
    a.getBoardOutlines()
    print(a.boardOutlines)
    a.getShapes()
    a.getComponents()
    a.getNets()
    a.getHoles()
    

    ## get data with interface
    #b = GenCADLoader()
    #b.loadSchematic('nexyM.gcd')
