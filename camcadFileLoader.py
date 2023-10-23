import os

class CamCADLoader():
    CIRCLE_DIMENSIONS = [(0.050, 0.050), (0.025, 0.025)]
    RECTANGLE_DIMENSIONS = [(-0.020, -0.016), (0.020, 0.016)] #[(0.039, 0.039), (0.013, 0.013)]

    def __init__(self):
        '''
        Creates CamCADLoader instance. Attributes:
            self.sections - dict of sections in file (sectionName:[sectionStart, sectionEnd], where sectionStart, sectionEnd are line's numbers)
            self.schematic  - list of lines in .cad file
            self.components - dict of components (componentName: [(x, y), side, case])
            self.holes - dict of TH holes (componentName: [(x, y), ...])
            self.nets - dict of nets (netName:{component:[pins]})
            self.pads - dict of pads (padName:[shape, (x1, y1), (x2, y2)])
            Returns dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        self.sections = {'CADFILEINFO':[],
                         'BOARDINFO':[],
                         'PARTLIST':[],
                         'NETLIST':[],
                         'PNDATA':[],
                         'TESTPOINT':[],
                         'PACKAGES':[],
                         'PAD':[],
                         'VARIANT':[],
                         'BOARDOUTLINE':[]}
        self.schematic = []
        self.components ={}
        self.holes ={}
        self.nets = {}
        self.pads = {}
        self.packages = {}
        self.boardOutlines = {'AREA':[], 'LINES':[], 'ARCS':[]}

    def loadSchematic(self, name, path='Schematic'):
        '''
        Opens a .cad file and returns dict of components, dict of nets, dict of pads and list of board vertexes. For manual processig of file use
        (openFile, getComponents, getNets, getPads, getPackages, getBoardOutlines, getHoles methods)
        '''
        self.openFile(name, path)
        nets = self.getNets()
        pads = self.getPads()
        components = self.getComponents()
        packages = self.getPackages()
        boardOutlines = self.getBoardOutlines()
        holes = self.getHoles()

        return components, nets, holes, boardOutlines, pads, packages

    def openFile(self, name, path='Schematic'):
        '''
        Opens a .cad file and creates a dict of sections (sectionName:[sectionStart, sectionEnd], where sectionStart, sectionEnd are line's numbers)
        '''
        ## get file path
        filePath = os.path.join(os.getcwd(), path, name)
        #print(filePath)

        ## open file and get line numbers that start and end sections
        with open(filePath, 'r') as file:
            for i, line in enumerate(file):
                line = line.replace('\n','')
                if line[1:] in self.sections or line[4:] in self.sections:
                    key = line.replace(':','').replace('END','')
                    self.sections[key].append(i)
                self.schematic.append(line)

        #print(self.schematic)
        #print(self.sections)

    def getComponents(self):
        '''
        Gets components from self.schematic. Iterates over PARTLIST Section (component data) and NETLIST section (casing data).
        Returns dict of components (componentName: [(x, y), side, case], where case is [caseName, caseShape, coords1, coords2])
        '''
        for i in self._getRange('PARTLIST'):
            line = self.schematic[i].split(',')
            try:
                componentName = line[1].replace(' ', '')
                try:
                    componentCoords = float(line[3]), float(line[4])
                except ValueError:
                    componentCoords = None, None
                componentSide = line[5]
                componentAngle = line[-1]
                self.components[componentName] = [componentCoords, componentSide, componentAngle]
            except IndexError:
                pass

        #print(self.pads)
        for i in self._getRange('NETLIST'):
            line = self.schematic[i].split(',')
            try:
                componentName = line[2].replace(' ', '')
                componentCaseID = int(line[-1])
                componentSide = line[-2].replace(' ', '')

                ## check if component is in dict and if it has proper coords
                if not componentName in self.components:
                    componentCoords = float(line[4]), float(line[5])
                    componentSide = line[6]
                    self.components[componentName] = [componentCoords, componentSide, 0]
                elif self.components[componentName][0] == (None, None):
                    componentCoords = float(line[4]), float(line[5])
                    self.components[componentName][0] = componentCoords

                ## update casing info
                if len(self.components[componentName]) == 3:
                    if componentCaseID in self.pads:
                        self.components[componentName] += [self.pads[componentCaseID]]
                    else:
                        self.components[componentName] += [['_','CIRCLE'] + CamCADLoader.CIRCLE_DIMENSIONS]

                ##
                if self.components[componentName][1] not in ('T', 'B'):
                    self.components[componentName][1] = componentSide
            except IndexError:
                pass

        return self.components

    def getHoles(self):
        '''
        Gets holes from self.schematic. Iterates over NETLIST Section.
        Returns dict of holes (holeName: [(x1, y1), (x2, y2)...])
        '''
        for i in self._getRange('NETLIST'):
            line = self.schematic[i].split(',')
            try:
                pinName = line[2].replace(' ', '')
                pinType = line[3].replace(' ', '')
                componentCoords = float(line[4]), float(line[5])
                pinSide = line[-2].replace(' ', '')
                if pinSide not in ('T', 'B'):
                    if not pinName in self.holes:
                        self.holes[pinName] = []
                    self.holes[pinName].append(componentCoords)
            except IndexError:
                pass

        return self.holes

    def getNets(self):
        '''
        Gets components from self.schematic. Iterates over NETLIST Section.
        Returns dict of nets (netName:{component:[pins]})
        '''
        for i in self._getRange('NETLIST'):
            line = self.schematic[i].split(',')
            try:
                netName = line[1].replace(' ', '')
                componentName = line[2].replace(' ', '')
                componentPin = line[3].replace(' ', '')

                if netName not in self.nets:
                    self.nets[netName] = {}
                if componentName not in self.nets[netName]:
                    self.nets[netName][componentName] = []
                self.nets[netName][componentName].append(componentPin)
            except IndexError:
                pass

        return self.nets

    def getPads(self):
        '''
        Gets pads from self.schematic. Iterates over PAD Section. SHOULD RUN BEFORE getComponents
        Returns dict of pads (padID:[padName, padShape, (x1, y1), (x2, y2)])
        '''
        for i in self._getRange('PAD'):
            line = self.schematic[i].split(',')
            try:
                padID = int(line[0])
                padName = line[1].replace(' ', '')
                padShape = line[2].replace(' ', '')
                padCoords1 = float(line[3]), float(line[4])
                padCoords2 = float(line[5]), float(line[6])
                #padCoords = [padCoords1, padCoords2]
                padCoords = CamCADLoader.CIRCLE_DIMENSIONS if padShape == 'CIRCLE' else CamCADLoader.RECTANGLE_DIMENSIONS
                self.pads[padID] = [padName, padShape] + padCoords
            except (IndexError, ValueError):
                pass

        return self.pads

    def getPackages(self):
        '''
        Gets packges from self.schematic. Iterates over PAD Section.
        Returns dict of packages (package:[type, (x, y)])
        '''
        for i in self._getRange('PACKAGES'):
            line = self.schematic[i].split(',')
            try:
                packageName = line[0].replace(' ', '')
                packageType = line[1].replace(' ', '')
                packageCoords = float(line[2]), float(line[3])
                self.packages[packageName] = [packageType, packageCoords]
            except (IndexError, ValueError):
                pass
        return self.packages

    def getBoardOutlines(self):
        '''
        Gets components from self.schematic. Iterates over BOARDOUTLINE Section.
        Returns dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        for i in self._getRange('BOARDINFO'):
            line = self.schematic[i].split(',')
            try:
                bottomLeftCorner = float(line[2]), float(line[3])
                upperRightCorner = float(line[4]), float(line[5])
                self.boardOutlines['AREA'] = [bottomLeftCorner, upperRightCorner]
            except IndexError:
                pass

        for i in self._getRange('BOARDOUTLINE'):
            line = self.schematic[i].split(',')
            try:
                coords1 = float(line[1]), float(line[2])
                coords2 = float(line[3]), float(line[4])
                self.boardOutlines['LINES'].append([coords1, coords2])
            except IndexError:
                pass

        return self.boardOutlines

    def _getRange(self, sectionName):
        '''
        Helper method for getting range of a section. Returns range
        '''
        rangeStart = self.sections[sectionName][0]
        rangeEnd = self.sections[sectionName][1]

        return range(rangeStart, rangeEnd)

if __name__ == '__main__':
    ## get data manually
    a = CamCADLoader()
    a.openFile('gemis2.cad')
    a.getPads(); #print(a.pads)
    a.getComponents()
    a.getNets()
    a.getHoles()
    a.getPackages()
    a.getBoardOutlines()

    #print(a.boardOutlines)
    for key in a.components:
        #if a.components[key]:
        print(key, a.components[key])

    ## get data with interface
    b = CamCADLoader()
    b.loadSchematic('gemis2.cad')