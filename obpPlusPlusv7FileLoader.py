import os
import tarfile

class OdbPlusPlusv7FileLoader():
    CIRCLE_DIMENSIONS = [(0.050, 0.050), (0.025, 0.025)]
    RECTANGLE_DIMENSIONS = [(-0.020, -0.016), (0.020, 0.016)] #[(0.039, 0.039), (0.013, 0.013)]

    def __init__(self, testPointPrefix='TP'):
        '''
        Creates OdbPlusPlusv7FileLoader instance. 
            testPointPrefix -> unique string common for all testpoints
        Attributes:
            self.components - dict of components (componentName: [(x, y), side, case])
            self.holes - dict of TH holes (componentName: [(x, y), ...])
            self.nets - dict of nets (netName:{component:[pins]})
            self.boardOutlines -  dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        self.components ={}
        self.holes ={}
        self.nets = {}
        self.boardOutlines = {'AREA':[], 'LINES':[], 'ARCS':[]}
        self.testpointPrefix = testPointPrefix

    def loadSchematic(self, name, path='Schematic'):
        '''
        Opens a .tgz file and returns dict of components, dict of nets, dict of holes and list of board vertexes. For manual processig of file use
        (openFile, getComponents, getNets, getHoles, getBoardOutlines methods)
        '''
        self.getFile(name, path)        
        boardOutlines = self.getBoardOutlines()
        maxX = self.findComponentLayerScale()
        scalingFactor = boardOutlines['AREA'][1][0] / maxX if 'profile' not in self.dimensionFile else 1
        components, pins = self.getComponents(scalingFactor=scalingFactor)
        nets = self.getNets(pins)
        holes = self.getHoles()

        return components, nets, holes, boardOutlines, None, None

    def getFile(self, name, path='Schematic'):
        '''
        Sets self.filePath to chosen file and sets location of files with net list, components, holes and dimensions
        '''
        self.filePath = os.path.join(os.getcwd(), path, name)
        with tarfile.open(self.filePath, 'r') as file:
            self.tarNames = file.getnames()

        ## dict with partial path to needed files
        filesDict = {'netlists/cadnet/netlist':None,        # netlist file
                     'layers/comp_+_bot/components':None,   # components files
                     'layers/comp_+_top/components':None,
                     'layers/drill/features':None,          # holes file
                     'layers/outline/features':None,        # board dimension file
                     '/profile':None
                     }
        
        ## get path by matching partial path
        for fileSubstring in filesDict:
            for tarName in self.tarNames:
                if fileSubstring in tarName:
                    filesDict[fileSubstring] = tarName
                    break

        ## save needed paths to variables
        self.netListFile = filesDict['netlists/cadnet/netlist']
        self.componentsFilesList = [filesDict['layers/comp_+_bot/components'], filesDict['layers/comp_+_top/components']]
        self.holesFile = filesDict['layers/drill/features']
        self.dimensionFile = filesDict['layers/outline/features'] or filesDict['/profile']

    def getComponents(self, scalingFactor=1):
        '''
        Opens files inside .tgz file. Extracts data of components from '.../layers/comp_+_bot/components' and 'odbjob_v7/steps/stp/layers/comp_+_top/components'.
            testPointChars - string that is common for all testpoints

        Returns: 
            self.components - dict of components (componentName: [(x, y), side, [caseName, caseShape, (caseX1, caseY1), (caseX2, caseY2)]])
            componentPinsDict - dict '{pinX} {pinY}': [componentName, f'{pinNumber}'] 
        '''
        with tarfile.open(self.filePath, 'r') as file:
            componentPinsDict = {}
            for sideNumber, componentFile in enumerate(self.componentsFilesList):
                componentSide = 'B' if sideNumber == 0 else 'T'                
                ## file not present
                if not componentFile:
                    continue 
                with file.extractfile(componentFile) as extractedFile:
                    fileLines = (line.decode('utf-8').replace('\n', '') for line in extractedFile.readlines())
                    for i, line in enumerate(fileLines):
                        if '# CMP ' in line:
                            buffer = next(fileLines).split(' ')
                            componentCoords = float(buffer[2]) * scalingFactor, float(buffer[3]) * scalingFactor; 
                            componentAngle = float(buffer[4])
                            componentName = buffer[6]
                            caseName = ''
                            if self.testpointPrefix in componentName:
                                caseShape = 'CIRCLE'
                                caseDimensions = OdbPlusPlusv7FileLoader.CIRCLE_DIMENSIONS
                            else:
                                caseShape = 'RECT'
                                caseDimensions = OdbPlusPlusv7FileLoader.RECTANGLE_DIMENSIONS
                            caseData = [caseName, caseShape] + caseDimensions
                            self.components[componentName] = [componentCoords, componentSide, componentAngle, caseData]
                        elif 'TOP' in line:
                            buffer = line.split(' ')
                            pinNumber = buffer[1]
                            try:
                                pinCoordsKey = f'{buffer[2]} {buffer[3]}'
                                componentPinsDict[pinCoordsKey] = [componentName, pinNumber]
                            except IndexError:
                                pass

        return self.components, componentPinsDict
    
    def findComponentLayerScale(self):
        '''
        Shity workaround about the fact that components are scaled down by some unkown factor (or rather I cant find the way to find it in better way).
        It iterates over the components file and finds minimum and maximum value of X coordinate. It is used to caclulate scaling factor.
        Returns abs(maxX - minX) - value close to the components layer width
        '''
        with tarfile.open(self.filePath, 'r') as file:
            maxX = float('-Inf')
            minX = float('Inf')
            for componentFile in self.componentsFilesList:
                ## file not present
                if not componentFile:
                    continue 
                with file.extractfile(componentFile) as extractedFile:
                    fileLines = (line.decode('utf-8').replace('\n', '') for line in extractedFile.readlines())
                    for i, line in enumerate(fileLines):
                        if '# CMP ' in line:
                            buffer = next(fileLines).split(' ')
                            maxX = max(maxX, float(buffer[2]))
                            minX = min(minX, float(buffer[2]))
        return abs(maxX - minX)
    
    def getHoles(self):
        '''
        Gets holes from '.../layers/drill/features' file of .tgz.
        Returns dict of holes (holeName: [(x1, y1), (x2, y2)...])
        '''
        with tarfile.open(self.filePath, 'r') as file:
            with file.extractfile(self.holesFile) as holesFile:
                holeNamesDict = {}
                fileLines = (line.decode('utf-8').replace('\n', '') for line in holesFile.readlines())
                for line in fileLines:
                    if len(line) > 0:
                        if line[0] == '&':
                            buffer = line.split(' ')
                            key = buffer[0][1:]
                            name = buffer[1]
                            holeNamesDict[key] = name
                        elif line[0] == 'P':
                            buffer = line.split(' ')
                            holeCoords = float(buffer[1]), float(buffer[2])
                            buffer = buffer[-1].split(';')[1]

                            ## assumed that .drill is always "1"
                            netType, drillType = buffer.split(',')[:2]
                            nameID = netType.split('=')[1]
                            netName = holeNamesDict[nameID]

                            ## 1=2 -> .drill=via, 1=1 ->.drill=not plated
                            if drillType in ('1=2','1=1') or 'VIA' in netName:
                                continue

                            if netName not in self.holes:                                
                                self.holes[netName] = []
                            self.holes[netName].append(holeCoords)
        return self.holes
    
    def getNets(self, componentPins):
        '''
        Gets components from '.../netlists/cadnet/netlist'. Use after getComponents method and pass componentPins from getComponents as input
        Returns dict of nets (netName:{component:[pins]})
        '''
        with tarfile.open(self.filePath, 'r') as file:
            with file.extractfile(self.netListFile) as netListFile:
                netnameDict = {}
                fileLines = (line.decode('utf-8').replace('\n', '') for line in netListFile.readlines())
                for line in fileLines:
                    if len(line) > 0:
                        if line[0] == '$':
                            buffer = line.split(' ')
                            key = buffer[0][1:]
                            name = buffer[1]
                            netnameDict[key] = name
                        elif line[0].isdigit():
                            buffer = line.split(' ')
                            netID = buffer[0]
                            pinCoords = f'{buffer[2]} {buffer[3]}'
            
                            netName = netnameDict[netID]
                            try:
                                componentName, componentPin = componentPins[pinCoords]
                            except KeyError:
                                continue
                            if netName not in self.nets:
                                self.nets[netName] = {}
                            if componentName not in self.nets[netName]:
                                self.nets[netName][componentName] = []
                            self.nets[netName][componentName].append(componentPin)
        return self.nets

    def getBoardOutlines(self):
        '''
        Opens file '.../layers/outline/features' or '.../profile' inside .tgz file and gets board shape data.
        Returns dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        if 'profile' in self.dimensionFile:
            minX, minY, maxX, maxY = self.extractProfileFile()
        else:
            with tarfile.open(self.filePath, 'r') as file:
                with file.extractfile(self.dimensionFile) as outlineFile:
                    fileLines = (line.decode('utf-8').replace('\n', '') for line in outlineFile.readlines())
                    
                    minX, minY = float('Inf'), float('Inf')
                    maxX, maxY = float('-Inf'), float('-Inf')
                    for line in fileLines:
                        if line and line[0] in ('A', 'L'):
                            buffer = line.split(' ')
                            shape = buffer[0]
                            if shape == 'A':
                                point1 = float(buffer[1]), float(buffer[2])
                                point2 = float(buffer[3]), float(buffer[4])
                                point3 = float(buffer[5]), float(buffer[6])
                                self.boardOutlines['ARCS'].append([point1, point2, point3])
                            elif shape == 'L':
                                point1 = float(buffer[1]), float(buffer[2])
                                point2 = float(buffer[3]), float(buffer[4])
                                self.boardOutlines['LINES'].append([point1, point2])

                                minX = min(minX, point1[0], point2[0])
                                maxX = max(maxX, point1[0], point2[0])
                                minY = min(minY, point1[1], point2[1])
                                maxY = max(maxY, point1[1], point2[1])

        self.boardOutlines['AREA'] = [(minX, minY), (maxX, maxY)]

        return self.boardOutlines
    
    def extractProfileFile(self):
        '''
        Opens file '.../profile' inside .tgz file and gets board shape data.
        Returns minX, minY, maxX, maxY
        '''
        with tarfile.open(self.filePath, 'r') as file:
            with file.extractfile(self.dimensionFile) as outlineFile:
                fileLines = (line.decode('utf-8').replace('\n', '') for line in outlineFile.readlines())

                minX, minY = float('Inf'), float('Inf')
                maxX, maxY = float('-Inf'), float('-Inf')
                pointCoordsQueue = []
                for line in fileLines:
                    if line and line[0] in ('O',):
                        buffer = line.split(' ')
                        shape = buffer[0]
                        if shape == 'OC':
                            point1 = pointCoordsQueue.pop(0)
                            point2 = float(buffer[1]), float(buffer[2])
                            point3 = float(buffer[3]), float(buffer[4])
                            self.boardOutlines['ARCS'].append([point1, point2, point3])

                            pointCoordsQueue.append(point3)
                        else:
                            try:
                                point = float(buffer[1]), float(buffer[2])
                            except IndexError:
                                continue
                            pointCoordsQueue.append(point)
                            if len(pointCoordsQueue) == 2:
                                point1, point2 = pointCoordsQueue
                                self.boardOutlines['LINES'].append([point1, point2])

                                minX = min(minX, point1[0], point2[0])
                                maxX = max(maxX, point1[0], point2[0])
                                minY = min(minY, point1[1], point2[1])
                                maxY = max(maxY, point1[1], point2[1])
                                pointCoordsQueue.pop(0)
        return minX, minY, maxX, maxY                     
            
if __name__ == '__main__':
    a = OdbPlusPlusv7FileLoader()
    a.getFile('odb_15020617_01.tgz') #660891125.tgz
    a.getBoardOutlines()
    a.getHoles()
    maxX = a.findComponentLayerScale()
    scalingFactor = a.boardOutlines['AREA'][1][0] / maxX
    _, pins = a.getComponents(scalingFactor=scalingFactor)
    a.getNets(pins)
    
    print(a.boardOutlines['AREA'], scalingFactor)

    #b = OdbPlusPlusv7FileLoader()
    #b.loadSchematic('odb_15020617_01.tgz')