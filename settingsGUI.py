import tkinter as tk
from tkinter import messagebox

class Settings(tk.Tk):
    def __init__(self, master=None, options=None, callback=None, callbackClose=None):
        super().__init__()
        self.resizable(False,False)
        self.title('Settings')

        if master:
            self.master = master
            self.withdraw()
        self.callback = callback
        self.callbackClose = callbackClose

        ## variables
        self.forceHolesCheckButtonVar = tk.IntVar()
        self.invertMarkerCheckButtonVar = tk.IntVar()

        # callback variables
        if options:
            self.componentsCustomScale, self.forceHoles, self.testPointPrefix = options
            self.forceHolesCheckButtonVar.set(int(self.forceHoles))
        else:
            self.componentsCustomScale = 1.0
            self.forceHoles = False
            self.testPointPrefix = 'TP'

        ## frames
        self.settingsFrame = tk.Frame(self.master)

        ## widgets
        self.customScaleLabel = tk.Label(self.settingsFrame, text="Set components' scale")
        self.customScaleEntry = tk.Entry(self.settingsFrame, width=8)
        self.customScaleEntry.insert(0, self.componentsCustomScale)
        self.forceHolesSizeLabel = tk.Label(self.settingsFrame, text="Don't change holes' radius")
        self.forceHolesSizeCheckbutton = tk.Checkbutton(self.settingsFrame, onvalue=1, offvalue=0, variable=self.forceHolesCheckButtonVar)
        self.closeButton = tk.Button(self.settingsFrame, text='Close and reload file', command=self.closeAndReload)
        self.testPointsLabel = tk.Label(self.settingsFrame, text="Testpoints' prefix")
        self.testPointsEntry = tk.Entry(self.settingsFrame, width=8)
        self.testPointsEntry.insert(0, self.testPointPrefix)


        ## position
        self.customScaleLabel.grid(row=0, column=0)
        self.customScaleEntry.grid(row=0, column=1)
        self.forceHolesSizeLabel.grid(row=1, column=0)
        self.forceHolesSizeCheckbutton.grid(row=1, column=1)
        self.testPointsLabel.grid(row=3, column=0)
        self.testPointsEntry.grid(row=3, column=1)
        self.closeButton.grid(row=4, column=0, columnspan=2, pady=(20, 10))

        self.settingsFrame.grid(row=0, column=0, padx=5, pady=5)

        self.bind('<Return>', lambda event: self.closeAndReload())

    def closeAndReload(self):
        '''
        Close application and pass data using callback function
        '''
        ## custom scale
        try:
            customScale = self.customScaleEntry.get()
            self.componentsCustomScale = float(customScale)
            if self.componentsCustomScale <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(title='Error', message=f'Scale must be positive number')
            self.componentsCustomScale = 1

        ## force holes
        self.forceHoles = self.forceHolesCheckButtonVar.get() == 1

        ## testpoints unique string
        self.testPointPrefix = self.testPointsEntry.get()

        settingsData = [self.componentsCustomScale, self.forceHoles, self.testPointPrefix]

        ## handle callbacks and closing
        if self.callback:
            self.callback(settingsData)

        if self.callbackClose:
            self.callbackClose(True)

        if self.master:
            self.master.destroy()
        else:
            self.destroy()




if __name__ == '__main__':
    settings = Settings()
    settings.mainloop()