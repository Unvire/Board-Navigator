import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from tkinter import font
from PIL import Image, ImageTk
from idlelib.tooltip import Hovertip
from datetime import datetime
import os
import pygame
import keyboard
import math

import schematicLoader
import drawBoardEngine
import mathFunctions
import settingsGUI
import aboutGUI

class BoardNavigator(tk.Tk):
    BASE_MARGIN = 90  # px 

    def __init__(self, master=None):
        super().__init__()
        self.resizable(False,False)
        self.title('Board Navigator')
        self.master = master

        ## variables
        # board variables
        self.filePath = ''
        self.image = None
        drawBoardEngine.Board.WIDTH = 1200
        drawBoardEngine.Board.HEIGHT = 700
        self.canvasOffset = (drawBoardEngine.Board.WIDTH // 2, drawBoardEngine.Board.HEIGHT // 2)
        self.drawSurface = pygame.Surface((drawBoardEngine.Board.WIDTH, drawBoardEngine.Board.HEIGHT))
        self.board = None
        self.components = None
        self.nets = None
        self.holes = None
        self.boardOutlines = None
        self.netComponents = []

        # drawing variables
        self.sideQueue = ['B', 'T']
        self.side = 'B'
        self.cursorPositionAbs = 0, 0
        self.previousAngle = 0
        self.moveVector = 0, 0
        self.markerData = None, (None, None), None, False
        self.cursor = False, None
        self.mouseCoords = None, None

        # settings
        self.componentsCustomScale = 1.0
        self.forceHoles = False
        self.testPointPrefix = 'TP'

        # states
        self.isMoveBoard = False
        self.isDrag = False
        self.isZoom = False
        self.isRotate = False

        ## frames
        self.mainFrame = tk.Frame()
        self.buttonsFrame = tk.Frame(self.mainFrame)
        self.netsFrame = tk.Frame(self.mainFrame)
        self.boardFrame = tk.Frame(self.mainFrame)
        self.findComponentFrame = tk.Frame(self.mainFrame)

        ## custom style for selection in treeview
        self.netTreeStyle = ttk.Style()
        self.netTreeStyle.map("Custom.Treeview", background=[("selected", "green")])

        ## widgets
        # buttons frame
        self.loadFileButton = tk.Button(self.buttonsFrame, text='Load file', command=self.openFile)
        self.settingsButton = tk.Button(self.buttonsFrame, text='Settings', command=self.openSettings, state='disabled')
        self.moveButton = tk.Button(self.buttonsFrame, text='Move', command=lambda: self.toggleMode('move'), state='disabled')
        self.zoomButton = tk.Button(self.buttonsFrame, text='Zoom', command=lambda: self.toggleMode('zoom'), state='disabled')
        self.rotateButton = tk.Button(self.buttonsFrame, text='Rotate', command=lambda: self.toggleMode('rotate'), state='disabled')
        self.changeSideButton = tk.Button(self.buttonsFrame, text='Change side', command=self.changeSide, state='disabled')
        self.clearMarkerButton = tk.Button(self.buttonsFrame, text='Clear marker', command=self.clearMarker, state='disabled')
        self.clearNetButton = tk.Button(self.buttonsFrame, text='Clear net', command=self.clearNet, state='disabled')
        self.defaultViewButton = tk.Button(self.buttonsFrame, text='Default view', command=self.setDefaultView, state='disabled')
        self.aboutButton = tk.Button(self.buttonsFrame, text='About', command=self.openAboutWindow)

        # nets frame
        self.netLabel = tk.Label(self.netsFrame, text='List of nets')
        self.netCollapseButton = tk.Button(self.netsFrame, text='Collapse all', command=self.collapseNetTree, state='disabled')
        self.netTree = ttk.Treeview(self.netsFrame, height=14, selectmode='browse', show='tree', style="Custom.Treeview")
        self.netTree.column('#0', width=210) # 210 is empirically the same as width 35
        self.netTreeScrollbar = tk.Scrollbar(self.netsFrame, command=self.scrollNets)
        self.componentsLabel = tk.Label(self.netsFrame, text='List of components')
        self.componentsListBox = tk.Listbox(self.netsFrame, width=35, height=14, selectmode='browse')
        self.componentsScrollbar = tk.Scrollbar(self.netsFrame, command=self.scrollComponents)
        self.componentPinsLabel = tk.Label(self.netsFrame, text='Pins of selected component')
        self.componentPinsTree = ttk.Treeview(self.netsFrame, height=10, selectmode='browse', columns=('Pin', 'Net'), show='headings')
        self.componentPinsTree.column('#1', width=105)
        self.componentPinsTree.column('#2', width=105)
        self.componentPinsScrollBar = tk.Scrollbar(self.netsFrame, command=self.scrollPins)

        # board frame
        self.imageCanvas = tk.Canvas(self.boardFrame, width=drawBoardEngine.Board.WIDTH, height=drawBoardEngine.Board.HEIGHT, bg='black')

        # find component frame
        self.findComponentByNameInfoLabel = tk.Label(self.findComponentFrame, text='Find component with its name')
        self.findComponentByNameEntry = tk.Entry(self.findComponentFrame, state='disabled')
        self.findComponentByNameButton = tk.Button(self.findComponentFrame, text='Find', command=self.findComponentByNameFromEntry, state='disabled')
        self.findComponentByClickInfoLabel = tk.Label(self.findComponentFrame, text='Clicked component:')
        self.findComponentByClickLabel = tk.Label(self.findComponentFrame, text='', font=font.Font(weight='bold'))
        self.currentlyDrawnSideInfoLabel = tk.Label(self.findComponentFrame, text='Current side:')
        self.currentlyDrawnSideLabel = tk.Label(self.findComponentFrame, text='', font=font.Font(weight='bold'))

        ## scrollbar parameters
        self.netTree.config(yscrollcommand=self.netTreeScrollbar.set)
        self.componentsListBox.config(yscrollcommand=self.componentsScrollbar.set)
        self.componentPinsTree.config(yscrollcommand=self.componentPinsScrollBar.set)

        ## position
        # widgets
        self.loadFileButton.grid(row=0, column=0, padx=5)
        self.settingsButton.grid(row=0, column=1,padx=(5, 35))
        self.moveButton.grid(row=0, column=2, padx=(35, 5))
        self.zoomButton.grid(row=0, column=3, padx=5)
        self.rotateButton.grid(row=0, column=4, padx=5)
        self.changeSideButton.grid(row=0, column=5, padx=(5, 35))
        self.clearMarkerButton.grid(row=0, column=6, padx=(35, 5))
        self.clearNetButton.grid(row=0, column=7, padx=5)
        self.defaultViewButton.grid(row=0, column=8, padx=(5,35))
        self.aboutButton.grid(row=0, column=9, padx=(35,5))

        self.netLabel.grid(row=0, column=0)
        self.netCollapseButton.grid(row=0, column=1, pady=5)
        self.netTree.grid(row=1, column=0, columnspan=2)
        self.netTreeScrollbar.grid(row=1, column=2, sticky='ns')
        self.componentsLabel.grid(row=2, column=0, columnspan=3, pady=(5,0))
        self.componentsListBox.grid(row=3, column=0, columnspan=2)
        self.componentsScrollbar.grid(row=3, column=2, sticky='ns')
        self.componentPinsLabel.grid(row=4, column=0, columnspan=3, pady=(5,0))
        self.componentPinsTree.grid(row=5, column=0, columnspan=2)
        self.componentPinsScrollBar.grid(row=5, column=2, sticky='ns')
        

        self.imageCanvas.grid(row=0, column=0)

        self.findComponentByNameInfoLabel.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.findComponentByNameEntry.grid(row=1, column=0, padx=(50, 5))
        self.findComponentByNameButton.grid(row=1, column=1, padx=(5, 50))
        self.findComponentByClickInfoLabel.grid(row=0, column=2, padx=50)
        self.findComponentByClickLabel.grid(row=1, column=2, padx=50)
        self.currentlyDrawnSideInfoLabel.grid(row=0, column=3, padx=50)
        self.currentlyDrawnSideLabel.grid(row=1, column=3, padx=50)

        # frames
        self.netsFrame.grid(row=0, column=0, rowspan=3, padx=5, pady=5)
        self.buttonsFrame.grid(row=0, column=1, padx=5, pady=5)
        self.findComponentFrame.grid(row=1, column=1, padx=5, pady=5)
        self.boardFrame.grid(row=2, column=1, padx=5, pady=5)

        self.mainFrame.grid(row=0, column=0)

        ## hovertips
        self.loadFileButtonHovertip = Hovertip(self.loadFileButton, 'Open cad file | (ctrl+o)')
        self.settingsButtonHovertip = Hovertip(self.settingsButton, 'Drawing settings')
        self.moveButtonHovertip = Hovertip(self.moveButton, 'Move board (hold LMB) | (q)')
        self.zoomButtonHovertip = Hovertip(self.zoomButton, 'Zoom in (LMB), zoom out (Shift+LMB) or scrollwheel | (w)')
        self.rotateButtonHovertip = Hovertip(self.rotateButton, 'Rotate 90deg (LMB), precise rotate (hold LMB) | (e)')
        self.changeSideButtonHovertip = Hovertip(self.changeSideButton, 'Change viewed side | (r)')
        self.clearMarkerButtonHovertip = Hovertip(self.clearMarkerButton, 'Clear arrow marker | (c)')
        self.clearNetButtonHovertip = Hovertip(self.clearNetButton, 'Clear marked components of the selected net | (v)')
        self.defaultViewButtonHovertip = Hovertip(self.defaultViewButton, 'Reset view to initial state')
        self.aboutButtonHovertip = Hovertip(self.aboutButton, 'About program')
        self.findComponentByNameButtonHovertip = Hovertip(self.findComponentByNameButton, 'Find component with given name')
        self.netCollapseButtonHovertip = Hovertip(self.netCollapseButton, 'Collapse the tree')

        ## binds
        self.bind('<Motion>', self.handleCursorMove)
        self.bind('<B1-Motion>', self.handleCursorDrag)
        self.bind('<ButtonPress-1>', self.handleCursorClick)
        self.bind('<ButtonRelease-1>', self.handleCurosrRelease)
        self.bind('<Return>', self.handleEnter)
        self.bind('<KeyPress-Shift_L>', lambda event: self.handleShift('press'))
        self.bind('<KeyRelease-Shift_L>', lambda event: self.handleShift('release'))
        self.bind('<MouseWheel>', lambda event: self.handleScrollWheel(event))

        # buttons
        self.bind('<q>', lambda event: self.toggleMode('move'))
        self.bind('<Q>', lambda event: self.toggleMode('move'))
        self.bind('<w>', lambda event: self.toggleMode('zoom'))
        self.bind('<W>', lambda event: self.toggleMode('zoom'))
        self.bind('<e>', lambda event: self.toggleMode('rotate'))
        self.bind('<E>', lambda event: self.toggleMode('rotate'))
        self.bind('<space>', lambda event: self.toggleMode('reset'))
        self.bind('<r>', lambda event: self.changeSide())
        self.bind('<R>', lambda event: self.changeSide())
        self.bind('<c>', lambda event: self.clearMarker())
        self.bind('<C>', lambda event: self.clearMarker())
        self.bind('<v>', lambda event: self.clearNet())
        self.bind('<V>', lambda event: self.clearNet())
        self.bind('<Control-o>', lambda event: self.loadSchematic())
        self.bind('<Control-O>', lambda event: self.loadSchematic())

    def _selectNetTreeItem(self, netName):
        '''
        Helper method for opening and highlighting self.netTree item
            netName - name of the net of currently drawn pcb
        '''
        ## scroll to net and open it        
        self.netTree.item(netName, open=True)
        self.netTree.see(netName)
        
        ## select item of netTree
        self.netTree.focus(netName)
        self.netTree.selection_set(netName)

    def _checkMmarkerOutsideScreen(self, markerCoords):
        '''
        Checks if marker is outside the screen and returns deltaX, deltaY vector that centers the view in current scale
        '''
        x, y = markerCoords
        deltaX, deltaY = 0, 0
        
        ## check if  marker is in the accepted subrectangle of the screen. If yes then do nothing, else change offsets so the marker is centered
        if (BoardNavigator.BASE_MARGIN < x + self.board.xMoveOffset < self.board.WIDTH - BoardNavigator.BASE_MARGIN and 
            BoardNavigator.BASE_MARGIN < y + self.board.yMoveOffset < self.board.HEIGHT - BoardNavigator.BASE_MARGIN):
                return 0, 0
        
        deltaX = (self.board.WIDTH // 2 - (x + self.board.xMoveOffset))
        deltaY = (self.board.HEIGHT // 2 - (y + self.board.yMoveOffset))
        return deltaX, deltaY
    
    def handleCursorMove(self, event):
        '''
        Gets cursor coords relative to the board when cursor is moved. Resets isDraw. Draws cursor outline
        '''
        x, y, widget = self.getCursorCoords(event)

        self.isDrag = False # reset isDrag variable, because this method is called when button1 is not held

        ## check if mouse if over canvas with board
        if widget != self.imageCanvas:
            cursor = None, None
            try:
                self.updateBoardLayer(cursor=cursor)
            except AttributeError:
                pass
            return

        self.mouseCoords = x, y
        ## set cursor outline parameters
        if self.isMoveBoard:
            cursor = (x, y), self.board.RED
        elif self.isZoom:
            if keyboard.is_pressed('shift'):
                cursor = (x, y), self.board.GRAY2
            else:
                cursor = (x, y), self.board.GRAY
        elif self.isRotate:
            cursor = (x, y), self.board.GREEN
        else:
            cursor = None, None

        if self.board:
            self.updateBoardLayer(cursor=cursor)

    def handleCursorDrag(self, event):
        '''
        Gets cursor x,y relative to the previous position if Button1 is held
        '''
        xAbs, yAbs, widget = self.getCursorCoords(event)

        x = self.cursorPositionAbs[0] - xAbs
        y = self.cursorPositionAbs[1] - yAbs
        self.cursorPositionAbs = xAbs, yAbs

        if widget != self.imageCanvas:
            return

        if not self.isDrag:
            self.isDrag = True # ignore first coords to avoid board teleporting (too big relative coords)
        elif self.isMoveBoard:
            cursor = (xAbs, yAbs), self.board.RED
            self.updateBoardLayer(deltaVector=(-x, -y), cursor=cursor)

        elif self.isRotate:
            ## calculate angle o
            invertX = self.side == 'T'
            midX, midY = mathFunctions.translate2D(self.board.translateMidPoint(), self.moveVector) # get midX, midY in screen coordinates
            currentAngle = math.atan2(yAbs - midY, xAbs - midX)
            deltaAngle = self.previousAngle - currentAngle # calculate change of angle
            self.previousAngle = currentAngle

            angle = self.board.rotationAngle
            if deltaAngle < 0:
                angle += 5
            elif deltaAngle > 0:
                angle -= 5
            self.board.setRotationAngle(angle)

            cursor = (xAbs, yAbs), self.board.GREEN
            self.updateBoardLayer(cursor=cursor)

    def handleCursorClick(self, event):
        '''
        Gets cursor coordinates relative to the board and calls self.canvasClicked, self.listboxClicked or self.netTreeClicked depending on the clicked widget
        '''
        if self.board:
            x, y, widget = self.getCursorCoords(event)

            if widget == self.imageCanvas and self.board:
                self.canvasClicked((x, y), event)
            elif widget == self.componentsListBox and self.board:
                self.listboxClicked()
            elif widget == self.netTree and self.board:
                self.netTreeClicked()
            elif widget == self.componentPinsTree and self.board:
                self.componentPinsTreeClicked()

    def canvasClicked(self, coords, event):
        '''
        Handles zooming, finding component by click(findes component, updates label and draws marker)
        '''
        if self.isZoom:
            zoomSign = '-' if keyboard.is_pressed('shift') else '+'
            self.updateBoardLayer(zoom=zoomSign, event=event)
        elif self.isRotate or self.isMoveBoard:
            ## do nothing
            pass
        else:
            clickedComponent, isHole = self.board.findComponentUsingClick(self.board.boardLayer, coords, self.side)
            if clickedComponent:
                self.generatePinsTable(clickedComponent)
                self.selectItemInListBox(clickedComponent)
                self.findComponentByClickLabel['text'] = f'{clickedComponent}'
                self.findComponentByClickLabel['bg'] = 'green2'

                ## draw mareker on clicked component
                markerData = self.findComponentByName(clickedComponent, isHole)
            else:
                self.findComponentByClickLabel['text'] = ''
                self.findComponentByClickLabel['bg'] = 'SystemButtonFace'
                markerData = None, (None, None), None, False
            self.updateBoardLayer(markerData=markerData)

    def handleCurosrRelease(self, event):
        '''
        Method is called everytime Button-1 is released. Rotates board 90 degrees if isDrag == False
        '''
        x, y, widget = self.getCursorCoords(event)

        if self.isRotate and widget == self.imageCanvas and not self.isDrag:
            angle = self.board.rotationAngle

            if angle % 90 == 0:
                angle += 90
                if angle == 360:
                    angle = 0
            else:
                if 0 <= angle < 90:
                    angle = 0
                elif 90 <= angle < 180:
                    angle = 90
                elif 180 <= angle < 270:
                    angle = 180
                else:
                    angle = 270
            self.board.setRotationAngle(angle)
            self.updateBoardLayer()

    def listboxClicked(self):
        '''
        Draws marker pointnig to the selected component in listbox
        '''
        try:
            componentName = self.componentsListBox.get(self.componentsListBox.curselection())

            isMarkerOnDrawnSide, markerCoords, _, _ = self.findComponentByName(componentName)
            markerData = True, markerCoords, componentName, False

            deltaX, deltaY = self._checkMmarkerOutsideScreen(markerCoords)
            forceChange = deltaX or deltaY # if deltaX or deltaY is no 0 forcefully change offset

            self.generatePinsTable(componentName)

            self.updateBoardLayer(changeSide=not isMarkerOnDrawnSide, markerData=markerData, deltaVector=(deltaX, deltaY), forceChange=forceChange)
        except tk._tkinter.TclError:
            return

    def netTreeClicked(self):
        '''
        Draws marker pointnig to the selected component in treeview
        '''
        currentItem = self.netTree.focus().split('\t')
        ## clicked on component
        try:
            componentName = currentItem[1]
            isMarkerOnDrawnSide, markerCoords,_ ,_ = self.findComponentByName(componentName)

            deltaX, deltaY = self._checkMmarkerOutsideScreen(markerCoords)
            forceChange = deltaX or deltaY # if deltaX or deltaY is no 0 forcefully change offset

            markerData = True, markerCoords, componentName, False
            
            self.generatePinsTable(componentName)
            self.selectItemInListBox(componentName)
            self.updateBoardLayer(changeSide=not isMarkerOnDrawnSide, markerData=markerData, deltaVector=(deltaX, deltaY), forceChange=forceChange)

        ## clicked on net name
        except IndexError:
            netName = ''.join(currentItem)
            selectedNetComponents = list(self.nets[netName].keys())

            componentList = []
            searchList = self.board.components + self.board.testPoints
            for component in searchList:
                if component.name in selectedNetComponents:
                    componentList.append((component.coords, component.side))

            markerData = None, (None, None), None, False
            self.updateBoardLayer(netComponents=componentList, markerData=markerData)

    def handleEnter(self, event):
        '''
        Handles ENTER button - draws marker if cursor is in findComponentFrame (component from entry) or in treeview(component from treeview) or in listbox(component in listbox)
        '''
        if self.board:
            _, _, widget = self.getCursorCoords(event)

            if widget == self.findComponentByNameEntry:
                self.findComponentByNameFromEntry()
            elif widget == self.componentsListBox and self.board:
                self.listboxClicked()
            elif widget == self.netTree and self.board:
                self.netTreeClicked()
            elif widget == self.componentPinsTree and self.board:
                self.componentPinsTreeClicked()

    def handleShift(self, state):
        '''
        Handles left shift key. Used for changing zoom border color when cursor doesn't move
        '''
        if self.isZoom:
            if state == 'press':
                cursorCoords, _ = self.cursor
                cursor = cursorCoords, self.board.GRAY2

                color = '#' + ''.join(str(hex(num)) for num in self.board.GRAY2).replace('0x', '')
                self.zoomButton['bg'] = color
            elif state == 'release':
                cursorCoords, _ = self.cursor
                cursor = cursorCoords, self.board.GRAY

                color = '#' + ''.join(str(hex(num)) for num in self.board.GRAY).replace('0x', '')
                self.zoomButton['bg'] = color
            self.updateBoardLayer(cursor=cursor)

    def handleScrollWheel(self, event):
        _, _, widget = self.getCursorCoords(event)
        if self.board and self.isZoom and widget == self.imageCanvas:
            if event.delta < 0:
                zoomSign = '-' # scroll down
            else:
                zoomSign = '+' # scroll up
            self.updateBoardLayer(zoom=zoomSign, event=event)

    def openFile(self):
        '''
        Opens a schematic. Returns file path for file
        '''
        #print(self.filePath)
        path = os.path.join(os.getcwd(), 'Schematic')
        schematicFile = filedialog.askopenfilename(title='Open schematic file', initialdir=path, filetypes=(('All files','*.*'), ('CAMCAD file','*.cad'), ('GENCAD file','*.gcd')))
        self.filePath = schematicFile        

        self.componentsCustomScale = 1
        self.forceHoles = False
        self.invertMarker = False
        self.testPointPrefix = 'TP'

        self.loadSchematic(path=self.filePath)

    def loadSchematic(self, path=None, forceHoles=False, testPointPrefix='TP'):
        '''
        Creates drawBoardEngine.Board instance and draws board on screen
            path - path of the schematic file
            forceHoles = True/False - if True holes have constant radius else they are scaled according to the testpoints' radius
            testPointPrefix - prefix that all testpoints begin with
        '''

        if not path:
            return

        ## clear data when file changed
        self.components = None
        self.nets = None
        self.holes = None
        self.boardOutlines = None

        ## clear label, listbox and treeviews
        self.findComponentByClickLabel['text'] = ''
        self.findComponentByClickLabel['bg'] = 'SystemButtonFace'
        self.componentsListBox.delete(0, tk.END)
        for net in self.netTree.get_children():
            self.netTree.delete(net)
        for item in self.componentPinsTree.get_children():
            self.componentPinsTree.delete(item)

        ## process schematic file
        if self.filePath:
            try:
                self.components, self.nets, self.holes, self.boardOutlines, _, _ = schematicLoader.SchematicLoader.loadSchematic(self.filePath, testPointPrefix)
            except (TypeError, IndexError, ValueError) as e:
                currentDateTime = datetime.now()
                currentDateTime = currentDateTime.strftime("%d.%m.%Y_%H-%M-%S")
                with open(f'Crash {currentDateTime}.txt', 'w') as log:
                    message = f'Error loading file: {self.filePath}.\nReason:{e.args}'
                    log.write(message)
            self.board = drawBoardEngine.Board(self.components, self.nets, self.holes, self.boardOutlines, forceHoles, testPointPrefix)
            self.board.setComponentsCustomScale(self.componentsCustomScale)

            self.setDefaultView()

            ## add items of treeview
            for netName in sorted(self.nets):
                components = sorted(self.nets[netName].keys())
                self.treeAddMainBranch(components, netName)
                for component in components:
                    pins = sorted(self.nets[netName][component])
                    branchID = f'{netName}\t{component}'
                    self.treeAddSubBranch(pins, branchID)

            ## add items to componentsListbox
            componentsList = [component for component in self.components]
            holesList = [hole for hole in self.holes]
            listboxItems = sorted(set([component for component in componentsList + holesList]))

            for i, item in enumerate(listboxItems):
                self.componentsListBox.insert(i, item)

            ## set drawn side label to bottom
            if self.side == 'B':
                self.currentlyDrawnSideLabel['text'] = 'BOTTOM'

            ## enable buttons
            self.settingsButton['state'] = 'normal'
            self.moveButton['state'] = 'normal'
            self.zoomButton['state'] = 'normal'
            self.rotateButton['state'] = 'normal'
            self.changeSideButton['state'] = 'normal'
            self.clearMarkerButton['state'] = 'normal'
            self.defaultViewButton['state'] = 'normal'
            self.findComponentByNameEntry['state'] = 'normal'
            self.findComponentByNameButton['state'] = 'normal'
            self.clearNetButton['state'] = 'normal'
            self.netCollapseButton['state'] = 'normal'

    def toggleMode(self, mode):
        '''
        Sets current mode to move, rotate or zoom. Changes color of corresponding button
        '''
        if mode == 'move' and self.board:
            self.isMoveBoard = not self.isMoveBoard
            color = '#' + ''.join(str(hex(num)) for num in self.board.RED).replace('0x', '')
            self.moveButton['bg'] = color if self.isMoveBoard else 'SystemButtonFace'

            self.isRotate = False
            self.rotateButton['bg'] = 'SystemButtonFace'

            self.isZoom = False
            self.zoomButton['bg'] = 'SystemButtonFace'

            color = self.board.RED
            cursor = self.cursor[0], color

        elif mode == 'rotate' and self.board:
            self.isRotate = not self.isRotate
            color = '#' + ''.join(str(hex(num)) for num in self.board.GREEN).replace('0x', '')
            self.rotateButton['bg'] = color if self.isRotate else 'SystemButtonFace'

            self.isMoveBoard = False
            self.moveButton['bg'] = 'SystemButtonFace'

            self.isZoom = False
            self.zoomButton['bg'] = 'SystemButtonFace'

            color = self.board.GREEN
            cursor = self.cursor[0], color

        elif mode == 'zoom' and self.board:
            self.isZoom = not self.isZoom
            color = '#' + ''.join(str(hex(num)) for num in self.board.GRAY).replace('0x', '')
            self.zoomButton['bg'] = color if self.isZoom else 'SystemButtonFace'

            self.isMoveBoard = False
            self.moveButton['bg'] = 'SystemButtonFace'

            self.isRotate = False
            self.rotateButton['bg'] = 'SystemButtonFace'

            color = self.board.GRAY
            cursor = self.cursor[0], color

        elif mode == 'reset' and self.board:
            self.isMoveBoard = False
            self.moveButton['bg'] = 'SystemButtonFace'

            self.isZoom = False
            self.zoomButton['bg'] = 'SystemButtonFace'

            self.isRotate = False
            self.rotateButton['bg'] = 'SystemButtonFace'
            cursor = ['reset']

        self.updateBoardLayer(cursor=cursor)

    def changeSide(self):
        '''
        Changes currently drawn side of the board
        '''
        if self.board:
            self.updateBoardLayer(changeSide=True)

    def clearMarker(self):
        '''
        Clears marker by overwriting it with: markerData =  None, (None, None), None, False. Clears findComponentByClickLabel
        '''
        if self.board:
            markerData = None, (None, None), None, False
            self.updateBoardLayer(markerData=markerData)
            self.findComponentByClickLabel['text'] = ''
            self.findComponentByClickLabel['bg'] = 'SystemButtonFace'

    def clearNet(self):
        '''
        Clears marked net components by overwriting self.netComponents with []
        '''
        if self.board:
            self.updateBoardLayer(netComponents=['reset'])

    def setDefaultView(self):
        '''
        Resets current state of the board to default view by setting move offsets to 0 and zoom coefficient to 1
        '''
        self.isMoveBoard = False
        self.moveButton['bg'] = 'SystemButtonFace'
        self.isRotate = False
        self.rotateButton['bg'] = 'SystemButtonFace'
        self.isZoom = False
        self.zoomButton['bg'] = 'SystemButtonFace'

        self.board.defaultView()

        x, y = self.moveVector
        deltaVector = -x, -y
        markerData = None, (None, None), None, False
        netComponents = ['reset']

        self.updateBoardLayer(deltaVector=deltaVector, markerData=markerData, netComponents=netComponents)

    def findComponentByNameFromEntry(self):
        '''
        Get component name from Entry. Draw marker if component exists
        '''
        componentName = self.findComponentByNameEntry.get()
        componentName = componentName.upper()

        isMarkerOnDrawnSide, markerCoords, _, isHole = self.findComponentByName(componentName)
        

        ## if component exists generate pins table
        if markerCoords[0] and markerCoords[1]:
            self.generatePinsTable(componentName)
            
        deltaX, deltaY = self._checkMmarkerOutsideScreen(markerCoords)
        forceChange = deltaX or deltaY # if deltaX or deltaY is no 0 forcefully change offset

        markerData = True, markerCoords, componentName, isHole
        
        changeSide = not isMarkerOnDrawnSide and componentName in self.components
        self.updateBoardLayer(changeSide=changeSide, markerData=markerData, deltaVector=(deltaX, deltaY), forceChange=forceChange)

    def findComponentByName(self, componentName, isHole=False):
        '''
        Returns marker data:
            True/False - is component placed on currently drawn side?
            markerCoords - (x, y) tuple where to draw marker
            componentName - name of the pointed component

        If componentName is not passed as attribute method reads from Entry. Otherwise uses passed componentName
        '''
        if isHole:
            for hole in self.board.holes:
                if hole.name == componentName:
                    xList = [x for x, y in hole.coords]
                    yList = [y for x, y in hole.coords]
                    xMid, yMid = sum(xList) / len(xList), sum(yList) / len(yList)
                    componentSide = 'B'
                    componentCoords = self.board.screenPoint(self.board.boardLayer, (xMid, yMid), self.side == 'T')
        else:
            componentCoords, componentSide = self.board.findComponentUsingName(self.board.boardLayer, componentName)
        
        markerData = self.side == componentSide, componentCoords, componentName, isHole
        return markerData

    def updateBoardLayer(self, changeSide=False, deltaVector=None, markerData=None, cursor=None, zoom=None, event=None, netComponents=[], forceChange=False):
        '''
        Interface for drawBoard method and modifies class atributes (self.sideQueue, self.side, self.moveVector, self.markerData, self.cursor)
            changeSide = True/ False
            deltaVector - tuple of (deltaX, deltaY) axis relative offsets
            markerData - True/False(True means that marker will be drawn), coords, componentName, isHole
            cursor - (x, y), (R, G, B)
            zoom - False, '+', or '-'
            event - tkinter event (for cursor coordinates to calculate zoom)
            netComponents - list of components that need to be highlighted
            forceChange - bool value that bypass limit of moveOffset change
        '''
        zoomChanged = False
        if zoom and event:
            x, y, _ = self.getCursorCoords(event)
            #print(x, y)
            deltaVector = self.board.zoom((x, y), sign=zoom)
            zoomChanged = True

        if changeSide:
            self.sideQueue.append(self.sideQueue.pop(0))
            self.side = self.sideQueue[0]

            # update label
            self.currentlyDrawnSideLabel['text'] = 'TOP' if self.side == 'T' else 'BOTTOM'

        if deltaVector:
            # default view
            if netComponents == ['reset']:
                self.moveVector = 0, 0
            else:
                self.moveVector = self.board.getSetMoveVector(deltaVector, forceChange)
        if markerData:
            self.markerData = markerData
        if cursor:
            if cursor == ['reset']:
                self.cursor = None, None
            else:
                self.cursor = cursor
        if netComponents:
            if netComponents == ['reset']:
                self.netComponents = []
            else:
                self.netComponents = netComponents
        
        self.drawBoard(self.side, self.markerData, self.cursor, zoomChanged, self.netComponents)

    def drawBoard(self, side, markerData, cursor, zoomChanged, netComponents):
        '''
        Draws board image into self.imageCanvas.
            side - board side ('T' or 'B')
            markerData = markerCoords, markerSide
                markerCoords - coordfs o marker arrow
                markerSide - boar sdide ('T' or 'B')
            cursor - 2 element sequence (None or (x, y), (R, G, B)) - mouseCoords, color
            zoomChanged = True/False - if True the marker position is recalculated
            netComponents = sequence of ((x, y), side) (x, y are coords from file to be recalculated into the screenPoint)

        1. Update all layers (create layers, update marker)
        2. Blit layers into one surface
        3. Convert: pygame surface -> RGB byte string -> PIL image -> ImageTk
        4. Update canvas
        '''
        markerSide, markerCoords, componentName, isHole = markerData

        ## 1. create pygame surfaces
        self.board.createLayers()

        ## update marker (if compoonent is a hole then forcefully draw it)
        if componentName:
            markerData = self.findComponentByName(componentName, isHole)
            markerSide, markerCoords, _, isHole = markerData
            markerSide = markerSide or isHole

        ## update surfaces
        boardLayerData = side, (markerSide, markerCoords)
        self.board.updateLayers(boardLayerData, cursor, netComponents)

        ## 2. blit into one surface
        self.board.renderImage(self.drawSurface)

        ## 3.convert pygame surface to PhotoImage
        rawImageString = pygame.image.tostring(self.drawSurface, 'RGB')
        imagePIL = Image.frombytes('RGB',
                                   (drawBoardEngine.Board.WIDTH, drawBoardEngine.Board.HEIGHT),
                                   rawImageString)
        self.image = ImageTk.PhotoImage(image=imagePIL)

        ## 4. update canvas
        self.imageCanvas.create_image(self.canvasOffset, image=self.image)

    def treeAddMainBranch(self, branchValues, branchName):
        '''
        Adds main branch to self.netTree (ttk Treeview) with subelements ID as '{parent}\t{value}' eg. parent is 'Europe', subelement is 'France' then ID will be 'Europe   France'
        '''
        parent = self.netTree.insert("", 'end', branchName, text=branchName)
        for value in branchValues:
            self.netTree.insert(parent, 'end', f'{parent}\t{value}', text=value)

    def treeAddSubBranch(self, subbranchVales, parentBranchID):
        '''
        Adds subbranch to self.netTree (ttk Treeview) with subelements ID as '{parent}\t{value}' eg. parent is 'Europe-France', subelement is 'Paris' then ID will be 'Europe   France  Paris'
        '''
        for value in subbranchVales:
            try:
                self.netTree.insert(parentBranchID, 'end', f'{parentBranchID}\t{value}', text=value)
            except tk._tkinter.TclError:
                pass

    def collapseNetTree(self):
        '''
        Collapses all items of self.netTree
        '''
        mainBranch = self.netTree.get_children()
        for branchName in mainBranch:
            self.netTree.selection_remove(branchName)
            subBranch = self.netTree.get_children(branchName)
            for itemName in subBranch:
                self.netTree.item(itemName, open=False)
            self.netTree.item(branchName, open=False)
    
    def openBranchNetTree(self, componentName):
        '''
        Collapses all netTree and then opens first levels of NetTree if component belongs to the net.
            componentName - name of component to be found in nets
        '''
        self.collapseNetTree()
        for netName in self.nets:
            if componentName in self.nets[netName]:
                self._selectNetTreeItem(netName)

    def generatePinsTable(self, componentName):
        '''
        Generates ttk treeview table for pins of the component PIN -> NET_NAME.
            componentName - name of component to be found in nets
        '''
        pinsData = []
        for net in self.nets:
            if componentName in self.nets[net]:
                pinsData.append((self.nets[net][componentName], net))
        
        pinsData = sorted(pinsData, key=lambda x: x[0])
        self.componentPinsTree.heading('Pin', text='Pin')
        self.componentPinsTree.heading('Net', text='Net')

        ## clear previous table
        for item in self.componentPinsTree.get_children():
            self.componentPinsTree.delete(item)
        
        ## generate table
        for pin, net in pinsData:
            self.componentPinsTree.insert('', tk.END, values=(pin, net))
        
        ## change label text
        self.componentPinsLabel['text'] = f'Pins of selected component ({componentName[:10]})'
    
    def componentPinsTreeClicked(self):
        '''
        Gets net name from clicked row in table and opens net from self.netTree
        '''
        try:            
            self.collapseNetTree()
            
            ## get net name
            clickedNet = self.componentPinsTree.focus()
            netName = self.componentPinsTree.item(clickedNet)['values'][1]
            
            ## select item of netTree and show subbranch
            self._selectNetTreeItem(netName)
            self.netTreeClicked()
        except IndexError:
            pass
    
    def selectItemInListBox(self, componentName):
        '''
        Check if item is in listbox and see it (scroll + highlight)
        '''
        try:
            self.componentsListBox.selection_clear(0, tk.END)
            itemIndex = list(self.componentsListBox.get(0, tk.END)).index(componentName)
            self.componentsListBox.see(itemIndex)
            self.componentsListBox.select_set(itemIndex)
        except ValueError:
            pass

    def scrollNets(self, *args):
        '''
        Assigns scrollbar to self.netTree
        '''
        self.netTree.yview(*args)

    def scrollComponents(self, *args):
        '''
        Assigns scrollbar to self.componentsListBox
        '''
        self.componentsListBox.yview(*args)
    
    def scrollPins(self, *args):
        '''
        Assigns scrollbar to self.componentPinsTree
        '''
        self.componentPinsTree.yview(*args)        

    def getCursorCoords(self, event):
        '''
        Returns cursor coords related to hovered widget and widget reference
        '''
        x = event.x
        y = event.y
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        return x, y, widget

    def openSettings(self):
        '''
        Opens settings window
        '''
        self.settingsWindow = tk.Toplevel(self.master)
        self.settingsWindow.protocol('WM_DELETE_WINDOW', lambda: self.closeSettings(True))
        self.settingsWindow.title('Settings')
        self.settingsWindow.grab_set()
        self.settingsWindow.focus()
        options = self.componentsCustomScale, self.forceHoles, self.testPointPrefix
        self.settingsInstance = settingsGUI.Settings(master=self.settingsWindow, options=options, callback=self.getSettings, callbackClose=self.closeSettings)

    def getSettings(self, options):
        '''
        Callback method to get passed data from settings window. Reloads the schematic
        '''
        self.componentsCustomScale, self.forceHoles, self.testPointPrefix = options
        self.loadSchematic(path=self.filePath, forceHoles=self.forceHoles, testPointPrefix=self.testPointPrefix)

    def closeSettings(self, destroyed=False):
        '''
        Close settings window and toplevel
        '''
        if destroyed:
            try:
                self.settingsWindow.destroy()
                self.settingsInstance.destroy()
            except AttributeError:
                pass

    def openAboutWindow(self):
        '''
        Opens about window
        '''
        self.aboutWindow = tk.Toplevel(self.master)
        self.aboutWindow.protocol('WM_DELETE_WINDOW', lambda: self.closeAboutWindow(True))
        self.aboutWindow.title('About')
        self.aboutWindow.grab_set()
        self.aboutWindow.focus()
        self.aboutInstance = aboutGUI.About(master=self.aboutWindow, callbackClose=self.closeAboutWindow)

    def closeAboutWindow(self, destroyed):
        '''
        Closes About window
        '''
        if destroyed:
            try:
                self.aboutWindow.destroy()
                self.aboutInstance.destroy()
            except AttributeError:
                pass

if __name__ == '__main__':
    app = BoardNavigator()
    app.mainloop()