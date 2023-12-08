## BOARD Navigator
## About
This program is portable clone of SPEA's BoardNavigator - tool supposed to help with viewing, fixing and measurements of pcbas.

## Requirements
- Min. resolution: 1500 x 900 px
- Device that can run python 3.11 64bit

## Main window
Main window is divided into three sections:
1. Buttons
2. Canva with drawn pcba 
3. Components and nets

## Buttons
1. "Load file" - loads a file in which pcba is defined. The program can run: .cad (CAMCAD), .gcd(GENCAD) and .tgz(ODB++).
**ODB++ files with archived features files (features.Z) are not supported**
2. Settings - opens a window in which some settings can be modified:
-- Set component's scale -> manually adjust scale of components by passing a number between 0 and +infinity. Use this when components have wrong scale compared to board outlines
-- Don't change hole radius -> if true then holes in board are scaled with radius of testpoints. 
-- Testpoint's prefix -> unique prefix for testpoints in pcba (typical value is TP, but can be any text)
3. Move -> hold and drag to move board across the canvas
4. Zoom -> scroll up or Left click - zoom in. Scroll down or left click + shift - zoom out
5. Rotate -> rotates board. One click -> rotate 90 degrees clockwise. Hold and drag cursor -> rotate around center point of the board 
6. Change side -> changes currently drawn side of pcba. Currently drawn side is in the label above the canvas
7. Clear marker -> clears red arrow marking a component
8. Clear net -> clears violet circles marking components on the same net
9. Default view -> centers board, resets zooming and clear markers
10. About -> displays about window

## Canva with drawn pcba
Pcba is drawn on the black bacground. White lines mean board outlines, green rectangles mean components, yellow circles/rectangles mean testpoints and blue circles mean holes.

## Components and nets
Components and nets can be accessed with different approaches. Selected component is always marked by red arrow marker.
a. finding component by click - click on component(on canvas or in the list) to see its name (in label above the canvas, in the list and in the label above "Pins of selected components table") and nets to which it belongs to.
b. finding component by name - write down component's name to mark it if it exists in the pcba. Searching is not case sensitive.
c. finding net - click on net (in the list of nets or pins of selected component). All components on that net will be marked with violet circle. In the "List of nets" all components on chosen net will be displayed. Clicking on any component in the list will mark it. List of nets can be collapes with clicking "Collapse all" button.

## Using the program
Program supports keyboard. List of keys:
- Q -> enable moving board (red mouse outline and button background color)
- W -> enable zooming board (grey mouse outline and button background color)
- E -> enable board rotation (green mouse outline and button background color)
- space -> disable move, zoom and rotation
- ctrl+o -> open schematic file
- c -> clear marker
- v -> clear nets

Components cannot be clicked on kanvas when any of the move, zoom and rotation is enabled.

---
## Used libraries
- tkinter -> window GUI
- pygame -> drawing pcba
- PIL -> bridge between pygame and tkinter

## Extracted data from files
First step is extracting infromation from file. Data extracted from schematic file are python's dict (JSON).
1. components = {componentName: [(x, y), side, angle, [caseName, caseShape, coords1, coords2]]}
    - x,y - coords of the component
    - side - 'T' or 'B' - side on which component is mounted
    - angle - rotation angle of component in degrees
    - caseName - ~~name from the pads info~~ not used
    - caseShape - CIRCLE or RECT
    - coords1, coords2 - coords of top-left and bottom-right coords of the rectangle or midlle point, edge point of the circle. Class constants are used for coords.
2. nets = {netName: {component: [pins]}}
    - component - name of the component
    - pins - pins of the component that belong to the netName
3. holes = {componentName: [(x, y), ...]}
    - componentName - name of the component (or name of the hole)
    - [(x, y), ] - list of tuple coords that make holes for one component 
4. boardOutlines = {'AREA':[(xMin, yMin), (xMax, yMax)], 
                'LINES':[[(x11, y11), (x12, y12)], [(x21, y21), (x22, y22)], ...], 
                'ARCS':[[(x11, y11), (x12, y12), (x13, y13)], ...]
}
'AREA' - list of 2 tuples with maximal and minimal value of each coords
'LINES' - list of lines. Line is defined as a list with 2 tuple coords (start and end point)
'ARCS' - list of arcs. Arc is defined as a list with 3 tuples coords (startPoint, endPoint, cirlceCenterPoint)

## Processed components data
Second step is processing the dictionaries - components and holes. 
1. Rectangular and circular components - result component is instance of ComponentRectangle or ComponentCircle classes. Both of them have common attributes:
angle - rotation angle in degrees 
side - side of component
coords - (x, y)
Attributes of ComponentRectangle:
    - points - list of (x, y) that describe case shape in pygame surface coords
    - collsionArea - [(xMin, yMin), (xMax, yMax)] - list of (x, y) tuples that defines rectangular area of colision

    Attributes of ComponentCircle:
    - radius - radius of the circle
    - collsionArea - [(xMin, yMin), (xMax, yMax)] - list of (x, y) tuples that defines rectangular area of colision (circle is inscribed into square)
2. Holes
Holes are parent class for the ones described above. They have only name and coords attributes

## Drawing the board
Third step is rendering the surface with the board
Process begins with convertion data from file to lists of objects described above (in constructor)
```
board = drawBoardEngine(components, nets, holes, boardOutlines, forceHoles=False, testPointPrefix='TP')
```
Then marker data and surfaces are updated. Order of rendering is: board outlines -> holes -> net circles *(if exists)* -> test points -> components -> marker *(if exists)*. Each rendering is iterating over list of parts and drawing them on surface as a demanded shape.
```
## update marker (if compoonent is a hole then forcefully draw it)
if componentName:
    markerData = self.findComponentByName(componentName, isHole)
    markerSide, markerCoords, _, isHole = markerData
    markerSide = markerSide or isHole

## update surfaces
boardLayerData = side, (markerSide, markerCoords)
board.updateLayers(boardLayerData, cursor, netComponents)
```

Last step is bliting boardSurface(with outlines, components, etc) and mouseLayer(with cursor outline) into one surface
```
board.renderImage(self.drawSurface)
```

## pygame surface in tkinter
In order to draw pygame surface in tkinter widget it must be converted several times: pygame surface -> byte string -> PIL's IMAGE -> ImageTK:
```
## Convert pygame surface to PhotoImage
rawImageString = pygame.image.tostring(self.drawSurface, 'RGB')
imagePIL = Image.frombytes('RGB',
                           (drawBoardEngine.Board.WIDTH, drawBoardEngine.Board.HEIGHT),
                           rawImageString)
self.image = ImageTk.PhotoImage(image=imagePIL)

## Update canvas
self.imageCanvas.create_image(self.canvasOffset, image=self.image)
```

## Possible Future updates
1. Rewriting data extracting scripts to use regular expressions
2. Handling archived features (features.Z) of .tgz
3. Handling more formats
4. Loading data from JSON (as it is base format for this program) and saving loaded file as JSON
5. Storing components layer as whole. Currently when moving each component is recalculated separately. Moving layer as a whole could be more efficient (I dont see performance issues now)