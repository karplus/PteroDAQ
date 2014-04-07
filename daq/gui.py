try:
    import tkinter as tk
    from tkinter import messagebox as tkm
    from tkinter import filedialog as tkf
    from tkinter import simpledialog as tks
    from tkinter import ttk
except ImportError:
    import Tkinter as tk
    import tkMessageBox as tkm
    import tkFileDialog as tkf
    import tkSimpleDialog as tks
    import ttk
import core
from getports import ports
from comm import tostr
import os.path
import sys

maindir = os.path.normpath(os.path.join(os.path.abspath(__file__), '../..'))

iswindows = sys.platform in ('win32', 'cygwin')

changerunning = False

def changetime(varname, varind, acc):
    """Update the seconds or hertz field
    when the other one is changed.
    """
    global changerunning
    if changerunning:
        changerunning = False
        return
    if varname == str(secvar):
        try:
            s = secvar.get()
            if s == 0:
                return
            changerunning = True
            hzvar.set(1/s)
        except ValueError:
            pass
    else:
        try:
            h = hzvar.get()
            if h == 0:
                return
            changerunning = True
            secvar.set(1/h)
        except ValueError:
            pass

class ImageButton(ttk.Label):
    """A button consisting of an image.
    Has no border except for that provided by the image.
    """
    def __init__(self, master, file, command=None):
        img = tk.PhotoImage(file=file)
        ttk.Label.__init__(self, master, image=img)
        self.img = img
        if command is not None:
            self.bind('<ButtonRelease-1>', command)

class Channel(ttk.Frame):
    chnums = {0}
    byloc = []
    slwidth = 200
    slheight = 50
    def __init__(self, master):
        def changeicon(val, *args):
            if val in anaset:
                pinchoice['image'] = sineimg
            else:
                pinchoice['image'] = squareimg
        tk.Frame.__init__(self, master)
        self.downsamp = 1
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label='Downsample', command=self.req_downsample)
        self.menu.add_command(label='Move Up', command=self.move_up)
        self.menu.add_command(label='Move Down', command=self.move_down)
        self.menu.add_command(label='Remove', command=self.remove)
        self.num = max(Channel.chnums) + 1
        Channel.chnums.add(self.num)
        Channel.byloc.append(self)
        self.namevar = nv = tk.StringVar()
        self.pinvar = pv = tk.StringVar()
        self.can = tk.Canvas(self, height=self.slheight, width=self.slwidth, highlightthickness=0)
        self.canline = self.can.create_line(0, 0, 0, 0)
        self.coords = []
        nv.set('ch{}'.format(self.num))
        namefield = ttk.Entry(self, textvariable=nv, width=16, font=('TkTextFont', 0, 'bold'))
        namefield.focus()
        pinchoice = tk.OptionMenu(self, pv, '')
        pinchoice['menu'].delete(0)
        for x in daq.board.analogs:
            pinchoice['menu'].add_command(label=x[0], image=sineimg, command=tk._setit(pv, x[0], changeicon), compound='left')
        for x in daq.board.digitals:
            if x[0] not in anaset:
                pinchoice['menu'].add_command(label=x[0], image=squareimg, command=tk._setit(pv, x[0], changeicon), compound='left')
        pinchoice['width'] = 100 if iswindows else 150
        pinchoice['compound'] = 'left'
        pinchoice['image'] = sineimg
        #delbutton = ImageButton(self, file=os.path.join(maindir, 'daq/icons/remove.gif'), command=self.remove)
        optbutton = ImageButton(self, file=os.path.join(maindir, 'daq/icons/options.gif'), command=self.show_options)
        pv.set(daq.board.analogs[0][0])
        namefield.grid(row=0, column=0, sticky='ew')
        pinchoice.grid(row=0, column=1)
        #delbutton.grid(row=0, column=2)
        optbutton.grid(row=0, column=2)
        self.can.grid(row=0, column=4)
        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=4, sticky='ew', padx=2, pady=2)
    def remove(self, e=None):
        Channel.chnums.discard(self.num)
        Channel.byloc.remove(self)
        self.destroy()
        channels.update_idletasks()
        outcchs['scrollregion'] = (0,0,channels.winfo_width(), channels.winfo_height())
    def add_data(self, ds):
        del ds[:-self.slwidth]
        if self.pinvar.get() in anaset:
            ds = [d/65536 for d in ds]
            if self.pinvar.get() in daq.board.analog_signed:
                ds = [d+0.5 for d in ds]
        ds = [(self.slheight-1)*d for d in ds]
        c = self.coords
        if not c:
            c[:] = [0, self.slheight-1-ds[0]]
            for n, x in enumerate(ds):
                c.append(n)
                c.append(self.slheight-1-x)
        else:
            del c[:-(self.slwidth+len(ds))*2]
            if c[0]:
                for n in range(0, len(c), 2):
                    c[n] -= len(ds)
            for n, d in enumerate(ds, c[-2]+1):
                c.append(n)
                c.append(self.slheight-1-d)
        self.can.coords(self.canline, *c)
    def clear(self):
        self.coords = []
        self.can.coords(self.canline, 0, 0, 0, 0)
    def show_options(self, e):
        self.menu.post(e.x_root, e.y_root)
    def req_downsample(self, e=None):
        res = tks.askinteger('Downsampling', 'Downsample channel {} by'.format(self.namevar.get()), initialvalue=self.downsamp, minvalue=1)
        if res is not None:
            self.downsamp = res
    def move_up(self, e=None):
        ind = Channel.byloc.index(self)
        if ind == 0:
            return
        sib = Channel.byloc[ind-1]
        Channel.byloc[ind] = sib
        Channel.byloc[ind-1] = self
        for ch in Channel.byloc:
            ch.pack_forget()
        for ch in Channel.byloc:
            ch.pack()
    def move_down(self, e=None):
        ind = Channel.byloc.index(self)
        if ind == len(Channel.byloc)-1:
            return
        sib = Channel.byloc[ind+1]
        Channel.byloc[ind] = sib
        Channel.byloc[ind+1] = self
        for ch in Channel.byloc:
            ch.pack_forget()
        for ch in Channel.byloc:
            ch.pack()
        

class PortSelect(object):
    def __init__(self, win, cb):
        win.title('Select a port')
        self.cb = cb
        self.f = f = ttk.Frame(win)
        self.pl = ttk.Treeview(f, show='tree', selectmode='browse', height=8)
        self.updateports()
        btn = ttk.Button(f, text='Go', command=self.useport)
        self.pl.pack(fill='both', expand='yes')
        btn.pack()
        f.pack(fill='both', expand='yes')
    def useport(self):
        port = self.ps[int(self.pl.selection()[0])][1]
        self.f.destroy()
        self.pl.after_cancel(self.aft)
        self.cb(tostr(port))
        self.aft = root.after(100, self.checkstart)
    def updateports(self):
        ps = self.ps = ports()
        portlist = self.pl
        fc = portlist.selection()
        if fc:
            fcn = portlist.item(int(fc[0]))['text']
        else:
            fcn = None
        for x in portlist.get_children():
            portlist.delete(x)
        for n, x in enumerate(ps):
            nm = tostr(x[0])
            portlist.insert('', 'end', str(n), text=x[0])
            if nm == fcn:
                portlist.selection_set(str(n))
        self.aft = portlist.after(500, self.updateports)
    def checkstart(self):
        if startmain.go:
            main()
        else:
            root.after(100, self.checkstart)

def startmain():
    startmain.go = True
startmain.go = False

def doconn(port):
    daq.connect(port, startmain)

def main(e=None):
    global anaset
    global sineimg
    global squareimg
    global secvar
    global hzvar
    global channels
    global outcchs
        
    f = ttk.Frame(root)
    root.title('Data Acquisition')
    anaset = {x[0] for x in daq.board.analogs}

    sineimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/sinewave.gif'))
    squareimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/squarewave.gif'))

    outfchs = ttk.Frame(f)
    outcchs = tk.Canvas(outfchs)
    controls = ttk.Frame(f)
    triggers = ttk.Frame(f)
    notes = ttk.Frame(f)
    channels = ttk.Frame(outfchs)
    outcchs.create_window(0, 0, anchor='nw', window=channels)

    def makeconf():
        conf = (core.TriggerTimed(secvar.get()) if triggertype.get() == 0 else core.TriggerPinchange(pinvar.get(), edgevar.get()),
            'Power', avgvar.get(),
            [core.AnalogChannel(ch.namevar.get(), ch.pinvar.get(), (ch.pinvar.get() in daq.board.analog_signed), ch.downsamp)
                if ch.pinvar.get() in anaset else
                core.DigitalChannel(ch.namevar.get(), ch.pinvar.get(), ch.downsamp)
                for ch in Channel.byloc])
        return conf
    def newchannel(e=None):
        ch = Channel(channels)
        ch.pack()
        ch.update_idletasks()
        outcchs['scrollregion'] = (0,0,channels.winfo_width(), channels.winfo_height())
        outcchs.update_idletasks()
        outcchs.yview_moveto(1)
    def startrec(e=None):
        statelabel['text'] = 'Recording'
        conf = makeconf()
        daq.config(conf)
        daq.go()
    def pauserec(e=None):
        statelabel['text'] = 'Paused'
        daq.stop()
    def oneread(e=None):
        daq.config(makeconf())
        daq.oneread()
    def clearreads(e=None):
        if tkm.askyesno(message='Clear all current readings?', icon='question'):
            daq.clear()
            for ch in channels.winfo_children():
                ch.clear()
            countlabel['text'] = '0'
    def savefile(e=None):
        pauserec()
        fn = tkf.asksaveasfilename(defaultextension='.txt')
        if fn is not None:
            daq.save(fn, notesbox.get('1.0', 'end'), powervar.get())

    statelabel = ttk.Label(controls, text='Paused', font=('TkTextFont', 0, 'bold'), width=12)
    countlabel = ttk.Label(controls, text='0')
    recbutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/record.gif'), command=startrec)
    pausebutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/pause.gif'), command=pauserec)
    addchbutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/plus.gif'), command=newchannel)
    singlebutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/one.gif'), command=oneread)
    clearbutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/trash.gif'), command=clearreads)
    savebutton = ttk.Button(controls, command=savefile, text='Save')
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
    savebutton.grid(row=0, column=6)
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
    powervar = tk.IntVar()
    avgvar = tk.IntVar()
    secvar.set(0.1)
    hzvar.set(10)
    avgvar.set(32)
    powervar.set(1)
    secvar.trace('w', changetime)
    hzvar.trace('w', changetime)
    timetrigger = ttk.Radiobutton(triggers, text='Timed', variable=triggertype, value=0)
    pintrigger = ttk.Radiobutton(triggers, text='Pin Change', variable=triggertype, value=1)
    seclabel = ttk.Label(triggers, text='sec')
    hzlabel = ttk.Label(triggers, text='Hz')
    secfield = ttk.Entry(triggers, textvariable=secvar, width=8)
    hzfield = ttk.Entry(triggers, textvariable=hzvar, width=8)
    #pinfield = tk.OptionMenu(triggers, pinvar, *(x[0] for x in daq.board.eint))
    #edgefield = tk.OptionMenu(triggers, edgevar, *(x[0] for x in daq.board.intsense))
    pinfield = ttk.Combobox(triggers, textvariable=pinvar, values=[x[0] for x in daq.board.eint])
    edgefield = ttk.Combobox(triggers, textvariable=edgevar, values=[x[0] for x in daq.board.intsense])
    pinfield['width'] = 8
    edgefield['width'] = 8
    pinvar.set(daq.board.eint[0][0])
    edgevar.set(daq.board.intsense[0][0])
    powerlabel = ttk.Checkbutton(triggers, text='Supply voltage: {:.4}'.format(daq.board.power_voltage), variable=powervar)
    avglabel = ttk.Label(triggers, text='x Averaging')
    avgfield = tk.OptionMenu(triggers, avgvar, *[1, 4, 8, 16, 32])
    avgfield['width'] = 5
    triggerlabel.grid(row=0, column=0, columnspan=4)
    timetrigger.grid(row=1, column=0, columnspan=4)
    pintrigger.grid(row=3, column=0, columnspan=4)
    seclabel.grid(row=2, column=1)
    hzlabel.grid(row=2, column=3)
    secfield.grid(row=2, column=0)
    hzfield.grid(row=2, column=2)
    pinfield.grid(row=4, column=0, columnspan=2)
    edgefield.grid(row=4, column=2, columnspan=2)
    powerlabel.grid(row=5, column=0, columnspan=4)
    avgfield.grid(row=6, column=1)
    avglabel.grid(row=6, column=2, columnspan=2)

    noteslabel = ttk.Label(notes, text='Notes', font=('TkTextFont', 0, 'bold'))
    notesbox = tk.Text(notes, height=6, width=60 if iswindows else 40, wrap='word', highlightthickness=0, font='TkTextFont')
    noteslabel.grid(row=0, column=0)
    notesbox.grid(row=1, column=0)

    def scrollcan(delta):
        delta = -int(delta)
        if delta >= 120 or delta <= -120:
            delta /= 120
        outcchs.yview_scroll(int(delta), 'units')

    addchbutton = ImageButton(controls, file=os.path.join(maindir, 'daq/icons/plus.gif'), command=newchannel)
    addchbutton.grid(row=0, column=3)
    addchlabel = ttk.Label(controls, text='Add Channel')
    addchlabel.grid(row=1, column=3)

    outbchs = ttk.Scrollbar(outfchs, orient='vertical', command=outcchs.yview)
    outcchs['yscrollcommand'] = outbchs.set

    controls.grid(row=0, column=0, columnspan=3, sticky='ew', padx=2, pady=2)
    ttk.Separator(f, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')
    triggers.grid(row=2, column=0)
    ttk.Separator(f, orient='vertical').grid(row=2, column=1, sticky='ns')
    notes.grid(row=2, column=2)
    ttk.Separator(f, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew')
    outcchs.grid(row=0, column=0, sticky='nsew')
    outbchs.grid(row=0, column=1, sticky='nse')
    outfchs.grid(row=4, column=0, columnspan=3, sticky='nsew')
    outfchs.columnconfigure(0, weight=1)
    f.pack(fill='y', expand=True)

    def update_data():
        newdat = daq.new_data()
        countlabel['text'] = int(countlabel['text']) + len(newdat)
        if newdat:
            for n, ch in enumerate(Channel.byloc, 1):
                ch.add_data([dat[n] for dat in newdat])
        root.after(100, update_data)
    
    root.update_idletasks()
    root.resizable(False, False)
    root.tk.createcommand('scrollcan', scrollcan)
    root.bind_all('<MouseWheel>', 'scrollcan %D')
    root.after(100, update_data)

root = tk.Tk()
daq = core.DataAcquisition()

ps = PortSelect(root, doconn)

root.mainloop()
