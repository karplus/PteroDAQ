import tkinter as tk
from tkinter import messagebox as tkm
from tkinter import ttk
import core

changerunning = False

def changetime(varname, varind, acc):
    global changerunning
    if changerunning:
        changerunning = False
        return
    if varname == str(secvar):
        s = secvar.get()
        if s == 0:
            return
        changerunning = True
        hzvar.set(1/s)
    else:
        h = hzvar.get()
        if h == 0:
            return
        changerunning = True
        secvar.set(1/h)

class Separator(ttk.Frame):
    def __init__(self, master, orient='h'):
        if orient.startswith('h'):
            ttk.Frame.__init__(self, master, height=2, bd=1, relief='sunken')
        elif orient.startswith('v'):
            ttk.Frame.__init__(self, master, width=2, bd=1, relief='sunken')

class ImageButton(ttk.Label):
    def __init__(self, master, file, command=None):
        img = tk.PhotoImage(file=file)
        ttk.Label.__init__(self, master, image=img)
        self.img = img
        if command is not None:
            self.bind('<ButtonRelease-1>', command)

class Channel(ttk.Frame):
    chnums = {0}
    def __init__(self, master):
        def changeicon(val, *args):
            if val in anaset:
                pinchoice['image'] = sineimg
            else:
                pinchoice['image'] = squareimg
        ttk.Frame.__init__(self, master)
        self.num = max(Channel.chnums) + 1
        Channel.chnums.add(self.num)
        self.namevar = nv = tk.StringVar()
        self.pinvar = pv = tk.StringVar()
        nv.set('ch{}'.format(self.num))
        namefield = ttk.Entry(self, textvariable=nv, width=16, font=('TkTextFont', 0, 'bold'))
        namefield.focus()
        pinchoice = tk.OptionMenu(self, pv, '')
        pinchoice['menu'].delete(0)
        anaset = set()
        for x in daq.board.analogs:
            pinchoice['menu'].add_command(label=x[0], image=sineimg, command=tk._setit(pv, x[0], changeicon), compound='left')
            anaset.add(x[0])
        for x in daq.board.digitals:
            if x[0] not in anaset:
                pinchoice['menu'].add_command(label=x[0], image=squareimg, command=tk._setit(pv, x[0], changeicon), compound='left')
        pinchoice['width'] = 150
        pinchoice['compound'] = 'left'
        pinchoice['image'] = sineimg
        delbutton = ImageButton(self, file='icons/remove.gif', command=self.remove)#tk.Button(self, text='X', command=self.remove, width=1)
        pv.set(daq.board.analogs[0][0])
        namefield.grid(row=0, column=0, sticky='ew')
        pinchoice.grid(row=0, column=1)
        delbutton.grid(row=0, column=2)
        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', padx=2, pady=2)
    def remove(self, e=None):
        Channel.chnums.discard(self.num)
        self.destroy()
        channels.update_idletasks()
        outcchs['scrollregion'] = (0,0,channels.winfo_width(), channels.winfo_height())

root = tk.Tk()
daq = core.DataAcquisition()

f = ttk.Frame(root)
root.title('Data Acquisition')

sineimg = tk.PhotoImage(file='icons/sinewave.gif')
squareimg = tk.PhotoImage(file='icons/squarewave.gif')

outfchs = ttk.Frame(f)
outcchs = tk.Canvas(outfchs)
controls = ttk.Frame(f)
triggers = ttk.Frame(f)
notes = ttk.Frame(f)
channels = ttk.Frame(outfchs)
outcchs.create_window(0, 0, anchor='nw', window=channels)

def newchannel(e=None):
    ch = Channel(channels)
    ch.pack()
    ch.update_idletasks()
    outcchs['scrollregion'] = (0,0,channels.winfo_width(), channels.winfo_height())
    outcchs.update_idletasks()
    outcchs.yview_moveto(1)
def startrec(e=None):
    statelabel['text'] = 'Recording'
    daq.config((TriggerTimed(secvar.get()) if triggertype.get() == 0 else TriggerPinchange(pinvar.get(), edgevar.get()),
        AnalogReference(1), []))
    daq.go()
    #statelabel['fg'] = '#800000'
def pausrec(e=None):
    statelabel['text'] = 'Paused'
    daq.stop()
    #statelabel['fg'] = '#000080'
def oneread(e=None):
    daq.oneread()
    #countlabel['text'] = int(countlabel['text'])+1
def clearreads(e=None):
    if tkm.askyesno(message='Clear all current readings?', icon='question'):
        countlabel['text'] = '0'

statelabel = ttk.Label(controls, text='Paused', font=('TkTextFont', 0, 'bold'), width=12)
countlabel = ttk.Label(controls, text='0')
recbutton = ImageButton(controls, file='icons/record.gif', command=startrec)
pausebutton = ImageButton(controls, file='icons/pause.gif', command=pausrec)
addchbutton = ImageButton(controls, file='icons/plus.gif', command=newchannel)
singlebutton = ImageButton(controls, file='icons/one.gif', command=oneread)
clearbutton = ImageButton(controls, file='icons/trash.gif', command=clearreads)
reclabel = ttk.Label(controls, text='Record')
pauselabel = ttk.Label(controls, text='Pause')
addchlabel = ttk.Label(controls, text='Add Channel')
singlelabel = ttk.Label(controls, text='Trigger Once')
clearlabel = ttk.Label(controls, text='Clear Data')
statelabel.grid(row=0, column=2)
countlabel.grid(row=1, column=2)
recbutton.grid(row=0, column=0)
pausebutton.grid(row=0, column=1)
addchbutton.grid(row=0, column=3)
singlebutton.grid(row=0, column=4)
clearbutton.grid(row=0, column=5)
reclabel.grid(row=1, column=0)
pauselabel.grid(row=1, column=1)
addchlabel.grid(row=1, column=3)
singlelabel.grid(row=1, column=4)
clearlabel.grid(row=1, column=5)

triggerlabel = ttk.Label(triggers, text='Trigger', font=('TkTextFont', 0, 'bold'))
triggertype = tk.IntVar()
secvar = tk.DoubleVar()
hzvar = tk.DoubleVar()
pinvar = tk.StringVar()
edgevar = tk.StringVar()
secvar.set(0.1)
hzvar.set(10)
secvar.trace('w', changetime)
hzvar.trace('w', changetime)
timetrigger = ttk.Radiobutton(triggers, text='Timed', variable=triggertype, value=0)
pintrigger = ttk.Radiobutton(triggers, text='Pin Change', variable=triggertype, value=1)
seclabel = ttk.Label(triggers, text='sec')
hzlabel = ttk.Label(triggers, text='Hz')
secfield = ttk.Entry(triggers, textvariable=secvar, width=8)
hzfield = ttk.Entry(triggers, textvariable=hzvar, width=8)
pinfield = tk.OptionMenu(triggers, pinvar, *(x[0] for x in daq.board.eint))
edgefield = tk.OptionMenu(triggers, edgevar, *(x[0] for x in daq.board.intsense))
pinfield['width'] = 8
edgefield['width'] = 8
pinvar.set(daq.board.eint[0][0])
edgevar.set(daq.board.intsense[0][0])
triggerlabel.grid(row=0, column=0, columnspan=4)
timetrigger.grid(row=1, column=0, columnspan=4)
pintrigger.grid(row=3, column=0, columnspan=4)
seclabel.grid(row=2, column=1)
hzlabel.grid(row=2, column=3)
secfield.grid(row=2, column=0)
hzfield.grid(row=2, column=2)
pinfield.grid(row=4, column=0, columnspan=2)
edgefield.grid(row=4, column=2, columnspan=2)

noteslabel = ttk.Label(notes, text='Notes', font=('TkTextFont', 0, 'bold'))
notesbox = tk.Text(notes, height=6, width=40, wrap='word', highlightthickness=0, font='TkTextFont')
noteslabel.grid(row=0, column=0)
notesbox.grid(row=1, column=0)

def scrollcan(delta):
    delta = -int(delta)
    if delta >= 120 or delta <= -120:
        delta /= 120.0
    outcchs.yview_scroll(delta, 'units')

addchbutton = ImageButton(controls, file='icons/plus.gif', command=newchannel)
addchbutton.grid(row=0, column=3)
addchlabel = ttk.Label(controls, text='Add Channel')
addchlabel.grid(row=1, column=3)

outbchs = ttk.Scrollbar(outfchs, orient='vertical', command=outcchs.yview)
outcchs['yscrollcommand'] = outbchs.set

controls.grid(row=0, column=0, columnspan=3, sticky='ew', padx=2, pady=2)
ttk.Separator(f, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')#, padx=2, pady=2)
triggers.grid(row=2, column=0)
ttk.Separator(f, orient='vertical').grid(row=2, column=1, sticky='ns')#, padx=2, pady=2)
notes.grid(row=2, column=2)
ttk.Separator(f, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew')#, padx=2, pady=2)
outcchs.grid(row=0, column=0, sticky='nsew')
outbchs.grid(row=0, column=1, sticky='nse')
outfchs.grid(row=4, column=0, columnspan=3, sticky='nsew')
outfchs.columnconfigure(0, weight=1)
#channels.grid(row=4, column=0, columnspan=3, sticky='ew')
f.pack(fill='y', expand=True)

root.update_idletasks()
root.resizable(False, False)
root.tk.createcommand('scrollcan', scrollcan)
root.bind_all('<MouseWheel>', 'scrollcan %D')

root.mainloop()
