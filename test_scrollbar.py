from tkinter import *

class scrollingFrame(Frame):
    def __init__(self, parentObject, background):
        Frame.__init__(self, parentObject, background = background)
        self.canvas = Canvas(self, borderwidth=0, background = background, highlightthickness=0)
        self.frame = Frame(self.canvas, background = background)

        self.vsb = Scrollbar(self, orient="vertical", command=self.canvas.yview, background=background)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(row=0, column=1, sticky=N+S)

        self.hsb = Scrollbar(self, orient="horizontal", command=self.canvas.xview, background=background)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.grid(row=1, column=0, sticky=E+W)

        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)
        self.window = self.canvas.create_window(0,0, window=self.frame, anchor="nw", tags="self.frame")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)


    def onFrameConfigure(self, event):
        #Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        #Resize the inner frame to match the canvas
        minWidth = self.frame.winfo_reqwidth()
        minHeight = self.frame.winfo_reqheight()

        if self.winfo_width() >= minWidth:
            newWidth = self.winfo_width()
            #Hide the scrollbar when not needed
            self.hsb.grid_remove()
        else:
            newWidth = minWidth
            #Show the scrollbar when needed
            self.hsb.grid()

        if self.winfo_height() >= minHeight:
            newHeight = self.winfo_height()
            #Hide the scrollbar when not needed
            self.vsb.grid_remove()
        else:
            newHeight = minHeight
            #Show the scrollbar when needed
            self.vsb.grid()

        self.canvas.itemconfig(self.window, width=newWidth, height=newHeight)

class messageList(object):
    def __init__(self, scrollFrame, innerFrame):
        self.widget_list = []
        self.innerFrame = innerFrame
        self.scrollFrame = scrollFrame

        # Keep a dummy empty row if the list is empty
        self.placeholder = Label(self.innerFrame, text=" ")
        self.placeholder.grid(row=0, column=0)

    # add new entry and update layout
    def add_message(self, text):
        print('add message')
        self.placeholder.grid_remove()
        # create var to represent states
        int_var = IntVar()

        cb = Checkbutton(self.innerFrame, text=text, variable=int_var)
        cb.grid(row=self.innerFrame.grid_size()[1], column=0, padx=1, pady=1, sticky='we')
        self.widget_list.append(cb)

        self.innerFrame.update_idletasks()
        self.scrollFrame.onCanvasConfigure(None)

    # delete all messages
    def del_message(self):
        print('del message')
        for it in self.widget_list:
            it.destroy()

        self.placeholder.grid()
        self.innerFrame.update_idletasks()
        self.scrollFrame.onCanvasConfigure(None)

deviceBkgColor = "#FFFFFF"
root = Tk() # Makes the window
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.wm_title("Title") # Makes the title that will appear in the top left
root.config(background = deviceBkgColor)

myFrame = scrollingFrame(root, background = deviceBkgColor)
myFrame.grid(row=0, column=0, sticky=N+S+E+W)

msgList = messageList(myFrame, myFrame.frame)

def new_message():
    test = 'Something Profane'
    msgList.add_message(test)


def del_message():
    msgList.del_message()

b = Button(root, text='New Message', command=new_message)
b.grid(row=1, column=0, sticky='we')

del_b = Button(root, text='Del Message', command=del_message)
del_b.grid(row=2, column=0, sticky='we')

root.mainloop() #start monitoring and updating the GUI