import tkinter as tk

class About(tk.Tk):
    def __init__(self, master=None, callbackClose=None):
        super().__init__()
        self.resizable(False, False)
        self.title('About')

        if master:
            self.master = master
            self.withdraw()
        self.callbackClose = callbackClose

        ## Frames
        self.textFrame = tk.Frame(self.master)

        ## Widgets
        self.text1Label = tk.Label(self.textFrame, text='Standalone free open source clone of Board Navigator by SPEA')
        self.text2Label = tk.Label(self.textFrame, text='Created by Krzysztof Balcerzak')
        self.closeButton = tk.Button(self.textFrame, text='Close', command=self.closeWindow)

        ## Positioning
        self.text1Label.grid(row=0, column=0, pady=5)
        self.text2Label.grid(row=1, column=0, pady=(5,10))
        self.closeButton.grid(row=2, column=0, pady=(10, 5))

        self.textFrame.grid(row=0, column=0, padx=5, pady=5)

    def closeWindow(self):
        if self.callbackClose:
            self.callbackClose(True)

        if self.master:
            self.master.destroy()
        else:
            self.destroy()

if __name__ == '__main__':
    app = About()
    app.mainloop()