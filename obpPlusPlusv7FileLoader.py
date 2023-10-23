import os
import tarfile

class OdbPlusPlusv7FileLoader():
    CIRCLE_DIMENSIONS = [(0.050, 0.050), (0.025, 0.025)]
    RECTANGLE_DIMENSIONS = [(-0.020, -0.016), (0.020, 0.016)] #[(0.039, 0.039), (0.013, 0.013)]

    def __init__(self):
        '''
        Creates OdbPlusPlusv7FileLoader instance. Attributes:
            self.components - dict of components (componentName: [(x, y), side, case])
            self.holes - dict of TH holes (componentName: [(x, y), ...])
            self.nets - dict of nets (netName:{component:[pins]})
            self.boardOutlines -  dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
        self.components ={}
        self.holes ={}
        self.nets = {}
        self.boardOutlines = {'AREA':[], 'LINES':[], 'ARCS':[]}

    def loadSchematic(self, name, path='Schematic'):
        '''
        Opens a .tgz file and returns dict of components, dict of nets, dict of holes and list of board vertexes. For manual processig of file use
        (openFile, getComponents, getNets, getHoles, getBoardOutlines methods)
        '''
        self.getFile(name, path)        
        boardOutlines = self.getBoardOutlines()
        maxX = self.findComponentLayerScale()
        scalingFactor = boardOutlines['AREA'][1][0] / maxX      
        components, pins = self.getComponents(scalingFactor=scalingFactor)
        nets = self.getNets(pins)
        holes = self.getHoles()

        return components, nets, holes, boardOutlines, None, None

    def getFile(self, name, path='Schematic'):
        '''
        Sets self.filePath to chosen file and sets location of files with net list, components, holes and dimensions
        '''
        self.filePath = os.path.join(os.getcwd(), path, name)
        self.netListFile = 'odbjob_v7/steps/stp/netlists/cadnet/netlist'
        self.componentsFilesList = ['odbjob_v7/steps/stp/layers/comp_+_bot/components', 'odbjob_v7/steps/stp/layers/comp_+_top/components']
        self.holesFile = 'odbjob_v7/steps/stp/layers/drill/features'
        self.dimensionFile = 'odbjob_v7/steps/stp/layers/outline/features'

    def getComponents(self, scalingFactor=1, testPointChars='TP'):
        '''
        Opens files inside .tgz file. Extracts data of components from 'odbjob_v7/steps/stp/layers/comp_+_bot/components' and 'odbjob_v7/steps/stp/layers/comp_+_top/components'.
            testPointChars - string that is common for all testpoints

        Returns: 
            self.components - dict of components (componentName: [(x, y), side, [caseName, caseShape, (caseX1, caseY1), (caseX2, caseY2)]])
            componentPinsDict - dict '{pinX} {pinY}': [componentName, f'{pinNumber}'] 
        '''
        with tarfile.open(self.filePath, 'r') as file:
            componentPinsDict = {}
            for sideNumber, compomentFile in enumerate(self.componentsFilesList):
                componentSide = 'B' if sideNumber == 0 else 'T'
                with file.extractfile(compomentFile) as extractedFile:
                    fileLines = (line.decode('utf-8').replace('\n', '') for line in extractedFile.readlines())
                    for i, line in enumerate(fileLines):
                        if '# CMP ' in line:
                            buffer = next(fileLines).split(' ')
                            componentCoords = float(buffer[2]) * scalingFactor, float(buffer[3]) * scalingFactor; 
                            componentAngle = float(buffer[4])
                            componentName = buffer[6]
                            caseName = ''
                            if testPointChars in componentName:
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
                            pinCoordsKey = f'{buffer[2]} {buffer[3]}'
                            componentPinsDict[pinCoordsKey] = [componentName, pinNumber]

        return self.components, componentPinsDict
    
    def findComponentLayerScale(self):
        '''
        Shity workaround about the fact that components are scaled down by some unkown factor (or rather I cant find the way to find it in better way).
        It iterates over the components file and finds maximum x coordinate of component. It is used to count scaling factor.
        Returns maxX - biggest absolute value of all the coordintates
        '''
        with tarfile.open(self.filePath, 'r') as file:
            maxX = float('-Inf')
            for sideNumber, compomentFile in enumerate(self.componentsFilesList):
                componentSide = 'B' if sideNumber == 0 else 'T'
                with file.extractfile(compomentFile) as extractedFile:
                    fileLines = (line.decode('utf-8').replace('\n', '') for line in extractedFile.readlines())
                    for i, line in enumerate(fileLines):
                        if '# CMP ' in line:
                            buffer = next(fileLines).split(' ')
                            maxX = max(maxX, abs(float(buffer[2])))
        return maxX
    
    def getHoles(self):
        '''
        Gets holes from 'odbjob_v7/steps/stp/layers/drill/features' file of .tgz.
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
                            buffer = buffer.split(',')[0]
                            nameID = buffer.split('=')[1]
                            netName = holeNamesDict[nameID]

                            ## skip VIA's
                            if 'VIA' in netName.upper():
                                continue

                            if netName not in self.holes:                                
                                self.holes[netName] = []
                            self.holes[netName].append(holeCoords)
        return self.holes
    
    def getNets(self, componentPins):
        '''
        Gets components from 'odbjob_v7/steps/stp/netlists/cadnet/netlist'. Use after getComponents method and pass componentPins from getComponents as input
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
        Opens file 'odbjob_v7/steps/stp/layers/outline/features' inside .tgz file and gets board shape data.
        Returns dict {'AREA':[(x1, y1), (x2, y2)], 'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]}
        '''
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
            
if __name__ == '__main__':
    a = OdbPlusPlusv7FileLoader()
    a.getFile('odbv7-1.tgz')
    a.getBoardOutlines()
    a.getHoles()
    maxX = a.findComponentLayerScale()
    scalingFactor = a.boardOutlines['AREA'][1][0] / maxX
    _, pins = a.getComponents(maxX=scalingFactor)
    a.getNets(pins)

    b = OdbPlusPlusv7FileLoader()
    b.loadSchematic('odbv7-1.tgz')