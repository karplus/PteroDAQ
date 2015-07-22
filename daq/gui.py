from __future__ import division, print_function

import os.path
import sys
from itertools import chain
from math import sqrt

try:
    import tkinter as tk
    from tkinter import messagebox as tkm
    from tkinter import filedialog as tkf
    from tkinter import simpledialog as tks
    from tkinter import ttk
    from tkinter import font as tkfont
except ImportError:
    import Tkinter as tk
    import tkMessageBox as tkm
    import tkFileDialog as tkf
    import tkFont as tkfont
    import tkSimpleDialog as tks
    import ttk
import core
from getports import ports
from comm import tostr


# TO DO:
#
#       Rename "PAUSE" to "STOP", since it can't be restarted
#       without resetting timer to 0?
#       
#       Any changes to configuration 
#           (except changes to notes or names of channels)
#           should prompt for "clear data"
#
#       Document all globals

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
            hzvar.set("{0:.4g}".format(1/s))
        except ValueError:
            pass
    else:
        try:
            h = hzvar.get()
            if h == 0:
                return
            changerunning = True
            secvar.set("{0:.4g}".format(1/h))
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

class ChannelWidget(ttk.Frame):
    chnums = set([0])
    byloc = []
    def __init__(self, master):
        def changeicon(val, *args):
            if daq.board.is_analog(val):
                pinchoice['image'] = sineimg
            elif daq.board.is_digital(val):
                pinchoice['image'] = squareimg
            else:
                pinchoice['image'] = sineimg    # BUG: new icon needed
        ttk.Frame.__init__(self, master)
        self.downsamp = 1
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label='Downsample', command=self.req_downsample)
        self.menu.add_command(label='Move Up', command=self.move_up)
        self.menu.add_command(label='Move Down', command=self.move_down)
        self.menu.add_command(label='Remove', command=self.remove)
        
        self.menu.add_separator()
        self.display_type=tk.StringVar()
        self.display_type.set('last value')
        self.display_type.trace('w',lambda *args:update_data(force_refresh=True))
        self.menu.add_radiobutton(label='last value', 
                variable=self.display_type,value='last value')
        self.menu.add_radiobutton(label='average', 
                variable=self.display_type,value='average')
        
        self.num = max(ChannelWidget.chnums) + 1
        ChannelWidget.chnums.add(self.num)
        ChannelWidget.byloc.append(self)
        
        # name of channel
        self.namevar = nv = tk.StringVar()
        nv.set('ch{}'.format(self.num))
        namefield = ttk.Entry(self, textvariable=nv, width=16, font=('TkTextFont', 0, 'bold'))
        namefield.focus()
        
        # which probe to use
        self.pinvar = pv = tk.StringVar()
        pv.set(daq.board.analogs[0][0]) 
        pinchoice = tk.OptionMenu(self, pv, '')
        pinchoice['menu'].delete(0)
        for x in daq.board.analogs:
            pinchoice['menu'].add_command(label=x[0], image=sineimg, command=tk._setit(pv, x[0], changeicon), compound='left')
        for x in daq.board.differentials:
            pinchoice['menu'].add_command(label=x[0], image=sineimg, command=tk._setit(pv, x[0], changeicon), compound='left')
        for x in daq.board.digitals:
            if not daq.board.is_analog(x[0]):   # BUG: suppresses digital channels with same names as analog channels
                pinchoice['menu'].add_command(label=x[0], image=squareimg, command=tk._setit(pv, x[0], changeicon), compound='left')
#        pinchoice['width'] = 100
        pinchoice['compound'] = 'left'
        pinchoice['image'] = sineimg
        pinchoice['bg']=os_background_color
        
        # options button
        optbutton = ImageButton(self, file=os.path.join(maindir, 'daq/icons/options.gif'), command=self.show_options)
        
        # canvas for sparkline
        self.sparkline_canvas = tk.Canvas(self, height=50, width=200, highlightthickness=0, 
                        bg='white')
        self.sparkline = self.sparkline_canvas.create_line(0, 0, 0, 0)

#        self.display_font = tkfont.Font(family="Courier",size=11)
        self.display_font= tkfont.Font(family="TkTextFont")
        self.average_label = ttk.Label(self,anchor='w',text="DC:\nRMS:",font=self.display_font)

        width_in_chars=int(0.999 + self.display_font.measure("65536.1")/self.display_font.measure('n'))
        self.display_value = ttk.Label(self,width=width_in_chars, anchor='e', font=self.display_font,justify='right')
        
        # 0th, 1st, and 2nd moment for computing mean and rms
        self.x0=0
        self.x1=0
        self.x2=0
        
        ## grid all the items
        namefield.grid(row=0, column=0, sticky='ew')
        self.columnconfigure(0, weight=1)       # let namefield stretch
        self.columnconfigure(3, minsize=10, weight=3)	# let sparkline stretch mode
        pinchoice.grid(row=0, column=1)
        optbutton.grid(row=0, column=2)
        self.sparkline_canvas.grid(row=0, column=3, sticky='ew')
        self.average_label.grid(row=0,column=4,sticky='ns')
        self.average_label.grid_forget()
        self.display_value.grid(row=0,column=5,sticky='ns')
        
        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=6,
                         sticky='ew', padx=2, pady=2)
    def remove(self, e=None):
        ChannelWidget.chnums.discard(self.num)
        ChannelWidget.byloc.remove(self)
        self.destroy()
        inner_channel_frame.update_idletasks()
        channel_canvas['scrollregion'] = (0,0,inner_channel_frame.winfo_width(), inner_channel_frame.winfo_height())
    
    def get_descriptor(self):
        """ return the descriptor used by the core for intepreting this channel
        """
        pin_name = self.pinvar.get()
        self.descriptor = core.ChannelDescriptor(name=self.namevar.get(),
                    probe= daq.board.probe_from_name[pin_name],
                    interpretation=core.Interpretation(
                        is_analog= daq.board.is_analog(pin_name) or daq.board.is_differential(pin_name),
                        is_signed=daq.board.is_differential(pin_name),
                        downsample=self.downsamp, 
                        gain=daq.board.gain_from_name[pin_name])
                    )
#        print("DEBUG: pin_name=", pin_name, "gain=", daq.board.gain_from_name[pin_name], file=sys.stderr)
        return self.descriptor
    
    def make_sparkline(self, chan_num, freeze_count):
        """Make a sparkline for data up to time point freeze_count
        from daq.data()[chan_num]
        (essentially daq.data()[freeze_count-width:freeze_count][chan_num])

        For analog channels, those are 16-bit unsigned values.
        For digital channels, those are 0 or 1.
        For differential channels, those are 16-bit signed values.
        """
#        print("DEBUG: sparkline(",chan_num,",",freeze_count,")", file=sys.stderr)
        if freeze_count==0:
            return
        
        x,y,width,height=self.grid_bbox(row=0,column=3)
        # make a copy of the data into sparkline, to transform in place
        start = max(0, freeze_count-width)
        sparkline = [x[chan_num] for x in daq.data()[start:freeze_count]]
#        print("DEBUG: len(sparkline)=",len(sparkline), file=sys.stderr)
        
        # update value at end of line
        if self.display_type.get()=='last value':
            self.average_label.grid_forget()
            last_value = sparkline[-1]
            if  self.descriptor.interpretation.is_analog and  use_power_voltage.get():
                last_value = self.descriptor.volts(last_value,daq.board.power_voltage)
                self.display_value['text']= "{0:.4f}".format(last_value)
            else:
                self.display_value['text']= last_value
        elif self.display_type.get()=='average':
            self.average_label.grid(row=0,column=4,sticky='ns')
            values = [x[chan_num] for x in daq.data()[self.x0:freeze_count]]
            self.x0 = freeze_count
            self.x1 += sum(values)
            self.x2 += sum(x*x for x in values)
            mean=self.x1/self.x0
            rms=sqrt(self.x2/self.x0 - mean**2)
            if  self.descriptor.interpretation.is_analog and  use_power_voltage.get():
                mean = self.descriptor.volts(mean,daq.board.power_voltage)
                rms = self.descriptor.volts(rms,daq.board.power_voltage)
                self.display_value['text']= "{0:7.4f}\n{1:7.4f}".format(mean,rms)
            else:
                self.display_value['text']= "{0:7.1f}\n{1:7.1f}".format(mean,rms)
        
        if len(sparkline)<2:
            return      # too short make a line
            
        # scale sparkline to 0..height-1 range
        # (more positive data is lower scaled value)
        if self.descriptor.interpretation.is_analog:
            if self.descriptor.interpretation.is_signed:
                for n,d in enumerate(sparkline):
                    sparkline[n] = (height-1)*(1.- (d+32768)/65536.)
            else:
                for n,d in enumerate(sparkline):
                    sparkline[n] = (height-1)*(1.- d/65536.)
        else:
            for n,d in enumerate(sparkline):
                sparkline[n] = (height-1)*(1- d)
        
        self.sparkline_canvas.coords(self.sparkline, *(chain.from_iterable(enumerate(sparkline))))
    
    def clear(self):
        self.sparkline_canvas.coords(self.sparkline, 0, 0, 0, 0)
        self.x0=0
        self.x1=0
        self.x2=0
        self.display_value['text']=''
    def show_options(self, e):
        self.menu.post(e.x_root, e.y_root)
    def req_downsample(self, e=None):
        res = tks.askinteger('Downsampling', 'Downsample channel {} by'.format(self.namevar.get()), initialvalue=self.downsamp, minvalue=1)
        if res is not None:
            self.downsamp = res
    def move_up(self, e=None):
        ind = ChannelWidget.byloc.index(self)
        if ind == 0:
            return
        sib = ChannelWidget.byloc[ind-1]
        ChannelWidget.byloc[ind] = sib
        ChannelWidget.byloc[ind-1] = self
        for ch in ChannelWidget.byloc:
            ch.pack_forget()
        for ch in ChannelWidget.byloc:
            ch.pack()
    def move_down(self, e=None):
        ind = ChannelWidget.byloc.index(self)
        if ind == len(ChannelWidget.byloc)-1:
            return
        sib = ChannelWidget.byloc[ind+1]
        ChannelWidget.byloc[ind] = sib
        ChannelWidget.byloc[ind+1] = self
        for ch in ChannelWidget.byloc:
            ch.pack_forget()
        for ch in ChannelWidget.byloc:
            ch.pack()
        

class PortSelect(object):
    def __init__(self, win, cb):
        win.title('Select a port')
        self.cb = cb
        self.port_frame = port_frame = ttk.Frame(win)
        self.pl = ttk.Treeview(port_frame, show='tree', selectmode='browse', height=8)
        self.updateports()
        btn = ttk.Button(port_frame, text='Go', command=self.useport)
        self.pl.pack(fill='both', expand='yes')
        btn.pack()
        port_frame.pack(fill='both', expand='yes')
    def useport(self):
        treeview_selections=self.pl.selection()
        if not treeview_selections:
            # nothing selected (probably no board plugged in)
            tkm.showerror("No board", "No PteroDAQ board selected---plug one in and try again")
            return
        port = self.ps[int(treeview_selections[0])][1]
        self.port_frame.destroy()
        self.pl.after_cancel(self.aft)
        self.cb(tostr(port))
        self.aft = root.after(100, self.checkstart)
    def updateports(self):
        ps = self.ps = ports()
        portlist = self.pl
        fc = portlist.selection()
        #print('DEBUG: fc =', repr(fc), file=sys.stderr)
        #print('DEBUG: ps =', repr(ps), file=sys.stderr)
        if fc:
            fcn = portlist.item(int(fc[0]))['text']
        elif ps:
            fcn = tostr(ps[0][0])
        else:
            fcn = None
        if isinstance(fcn, list): # python 3.4.3
            fcn = tostr(bytes(fcn))
        #print('DEBUG: fcn =', repr(fcn), file=sys.stderr)
        for x in portlist.get_children():
            portlist.delete(x)
        for n, x in enumerate(ps):
            nm = tostr(x[0])
            portlist.insert('', 'end', str(n), text=x[0])
            if nm == fcn:
                portlist.selection_set(str(n))
        self.aft = portlist.after(500, self.updateports)
    def checkstart(self):
        """A function to be scheduled by tkinter to check every 100ms
        to see if a connection to a DAQ has been made yet.
        
        Call main() on successful connection.
        """
        if startmain.go:
            # a daq.connect has completed
            if startmain.fail is None:
                # completed successfulyy
                main()
            else:
                # failed
                tkm.showerror('Error', startmain.fail)
                root.destroy()
        else:
            root.after(100, self.checkstart)    # schedule another check in 100ms

def startmain(fail=None):
    """The gui thread (in checkstart()) is monitoring startmain.go to say when 
    it should run. 
    If startmain.fail is not None, then it shows an error and dies.
    """
    startmain.fail = fail
    startmain.go = True

startmain.go = False

def doconn(port):
    daq.connect(port, startmain)

last_file_saved=None    # what filename was last used for a save operation


def main(e=None):
    global sineimg
    global squareimg
    global secvar
    global hzvar
    global use_power_voltage
    global inner_channel_frame
    global channel_canvas
    global clearreads
    global os_background_color
    global update_data
        
    try:
        # on Mac OS X, the background color for windows has a strange name
        # not supported on other platforms.
        root.winfo_rgb('systemSheetBackground')
        os_background_color = 'systemSheetBackground'
    except tk.TclError:
        # on other platforms the background is set already
        os_background_color = root['bg']
    
    master_frame = ttk.Frame(root)
    root.title('Data Acquisition')
    
    sineimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/sinewave.gif'))
    squareimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/squarewave.gif'))

    ## root:
    ##  Frame master_frame
    ##      Frame controls
    ##      Frame triggers
    ##      Frame notes
    ##      Frame channel_frame
    ##        Canvas chanel_canvas
    ##          Frame inner_channel_frame

    controls = ttk.Frame(master_frame)
    triggers = ttk.Frame(master_frame)
    notes = ttk.Frame(master_frame)
    channel_frame = ttk.Frame(master_frame)

    def makeconf():
        """Constructs a tuple for passing to DataAcquistion.config()
        consisting of (trigger, aref, avg, channel descriptors
        """
        trigger = core.TriggerTimed(secvar.get()) if triggertype.get() == 0 else core.TriggerPinchange(pinvar.get(), edgevar.get())
        aref = 'Power'
        avg = avgvar.get()
        inner_channel_frame =  [ ch.get_descriptor() for ch in ChannelWidget.byloc]
        return (trigger, aref, avg, inner_channel_frame)
    
    def newchannel(e=None):
        ch = ChannelWidget(inner_channel_frame)
        ch.pack(fill="x", expand=1)
        ch.update_idletasks()
        channel_canvas['scrollregion'] = (0,0,inner_channel_frame.winfo_width(), inner_channel_frame.winfo_height())
#        channel_canvas['width'] = inner_channel_frame.winfo_width()
        channel_canvas.update_idletasks()
        channel_canvas.yview_moveto(1)
    
    def power_voltage_str():
        return 'Supply voltage: {0:.4f}'.format(daq.board.power_voltage)
    def startrec(e=None):
        """Action to take when "Record" butting is pressed
        """
        if statelabel['text'] == 'Recording':
            # Don't restart if already recording.
            # This is questionable---restarting to get a new 0 time point
            # might be useful in marking human-observable events
            return
        statelabel['text'] = 'Recording'
        errorlabel.grid_forget()
        daq.config(makeconf())
        daq.go()
    def pauserec(e=None):
        """Action to take then "Pause" button is pressed
        """
        statelabel['text'] = 'Paused'
        daq.stop()
        powerlabel['text'] = power_voltage_str()
    def oneread(e=None):
        daq.config(makeconf())
        daq.oneread()
    def clearreads(e=None):
        if tkm.askyesno(message='Clear all current readings?', icon='question'):
            daq.clear()
            for ch in inner_channel_frame.winfo_children():
                ch.clear()
            countlabel['text'] = '0'
    
    def on_closing():
        """Code to run when user attempts to close window
        """
        if daq.num_saved < len(daq.data()):
            save_before_quit=tkm.askyesnocancel("{} unsaved readings".format(len(daq.data())),
                "Save before quitting?")
#            print("DEBUG: save_before_quit=",save_before_quit,file=sys.stderr)
            if save_before_quit is None:
                # cancel returns None
                return
            if save_before_quit:
                if not savefile():
                    return      # save dialog cancelled
        root.destroy()
        
    def savefile(e=None):
        """Asks if you want to save file, using last_file_saved
        as a suggestion.
        returns either filename saved into, or None (if save cancelled)
        """
        global last_file_saved
        pauserec()
        if last_file_saved:
            dir,file_base = os.path.split(last_file_saved)
            last_file_saved = tkf.asksaveasfilename(defaultextension='.txt',
                initialfile=file_base, initialdir=dir)
        else:
            last_file_saved = tkf.asksaveasfilename(defaultextension='.txt')
        if last_file_saved:
            daq.save(last_file_saved, notes=notesbox.get('1.0', 'end'), 
                convvolts = use_power_voltage.get(),
                new_conf=makeconf()
                )
        return last_file_saved
    
    ## define objects in controls Frame
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
    
    ## grid items in controls frame
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

    ## items in triggers Frame
    triggerlabel = ttk.Label(triggers, text='Trigger', font=('TkTextFont', 0, 'bold'))
    triggertype = tk.IntVar()
    secvar = tk.DoubleVar()
    hzvar = tk.DoubleVar()
    pinvar = tk.StringVar()
    edgevar = tk.StringVar()
    use_power_voltage = tk.IntVar()
    avgvar = tk.StringVar()
    secvar.set(0.1)
    hzvar.set(10)
    avgvar.set(daq.board.default_avg)
    use_power_voltage.set(1)
    secvar.trace('w', changetime)
    hzvar.trace('w', changetime)
    timetrigger = ttk.Radiobutton(triggers, text='Timed', variable=triggertype, value=0)
    pintrigger = ttk.Radiobutton(triggers, text='Pin Change', variable=triggertype, value=1)
    seclabel = ttk.Label(triggers, text='sec')
    hzlabel = ttk.Label(triggers, text='Hz')
    secfield = ttk.Entry(triggers, textvariable=secvar, width=8)
    hzfield = ttk.Entry(triggers, textvariable=hzvar, width=8)
    pinfield = ttk.Combobox(triggers, textvariable=pinvar, values=[x[0] for x in daq.board.eint])
    edgefield = ttk.Combobox(triggers, textvariable=edgevar, values=[x[0] for x in daq.board.intsense])
    pinfield['width'] = 8
    edgefield['width'] = 8
    pinvar.set(daq.board.eint[0][0])
    edgevar.set(daq.board.intsense[0][0])
    powerlabel = ttk.Checkbutton(triggers, text=power_voltage_str(), variable=use_power_voltage)
    if len(daq.board.avg) > 1:
        avglabel = ttk.Label(triggers, text='x Averaging')
        avgfield = tk.OptionMenu(triggers, avgvar, *(x[0] for x in daq.board.avg))
        avgfield['bg']=os_background_color
        avgfield['width'] = 5
    
    ## grid items in triggers Frame
    triggerlabel.grid(row=0, column=0, columnspan=4)
    timetrigger.grid(row=1, column=0, columnspan=2, sticky='w')
    secfield.grid(row=2, column=0, sticky='ew')
    seclabel.grid(row=2, column=1, sticky='w')
    hzfield.grid(row=2, column=2, sticky='ew')
    hzlabel.grid(row=2, column=3, sticky='w')
    pintrigger.grid(row=3, column=0, columnspan=2, sticky='w')
    pinfield.grid(row=4, column=0, columnspan=2, sticky='ew')
    edgefield.grid(row=4, column=2, columnspan=2, sticky='ew')
    powerlabel.grid(row=5, column=0, columnspan=4)
    if len(daq.board.avg) > 1:
        avgfield.grid(row=6, column=0, columnspan=2, sticky='e')
        avglabel.grid(row=6, column=2, columnspan=2, sticky='w')

    ## define items in notes frame
    errorlabel = ttk.Label(notes, text='Error: triggering too fast', foreground="red")
    noteslabel = ttk.Label(notes, text='Notes', font=('TkTextFont', 0, 'bold'))
    notesbox = tk.Text(notes, height=7, width=60 if iswindows else 40, wrap='word', highlightthickness=0, font='TkTextFont')

    ## grid items in notes frame
    noteslabel.grid(row=1, column=0)
    notesbox.grid(row=2, column=0, sticky='nsew')
    notes.columnconfigure(0,weight=1)
    notes.rowconfigure(2,weight=1)

    ## define items for channel_frame
    channel_canvas = tk.Canvas(channel_frame,
                   background= os_background_color,
                   highlightthickness=0)
    inner_channel_frame = ttk.Frame(channel_frame)      # must be after channel_canvas to layer on top
    inner_channel_window=channel_canvas.create_window(0, 0, anchor='nw', window=inner_channel_frame)
    channel_scrollbar = ttk.Scrollbar(channel_frame, orient='vertical', command=channel_canvas.yview)
    channel_canvas['yscrollcommand'] = channel_scrollbar.set

    # Weird way to allow inner_channel_frame to resize to fill canvas
    def inner_channel_change_width(event):
        """Function to bind to '<Configure>' of a canvas to make it adjust it's size
        when the window is resized.
        """
        canvas_width = event.width
        channel_canvas.itemconfig(inner_channel_window, width = canvas_width)

    channel_canvas.bind('<Configure>', inner_channel_change_width)
    
    def scrollcan(delta):
        delta = -int(delta)
        if delta >= 120 or delta <= -120:
            delta /= 120
        channel_canvas.yview_scroll(int(delta), 'units')

    ## grid items for channel_frame
    channel_canvas.grid(row=0, column=0, sticky='nsew')
    channel_scrollbar.grid(row=0, column=1, sticky='nse')
    channel_frame.columnconfigure(0, weight=1)
    channel_frame.rowconfigure(0, weight=1)

    ## grid items for master frame 
    controls.grid(row=0, column=0, columnspan=3, sticky='ew', padx=2, pady=2)
    ttk.Separator(master_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')
    triggers.grid(row=2, column=0, sticky='w')
    ttk.Separator(master_frame, orient='vertical').grid(row=2, column=1, sticky='nsw')
    notes.grid(row=2, column=2, sticky="nsew")
    ttk.Separator(master_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew')
    channel_frame.grid(row=4, column=0, columnspan=3, sticky='nsew')
    
    master_frame.rowconfigure(4,weight=1)       # let channel_frame stretch vertically
    master_frame.columnconfigure(0,weight=1)    # let controls and channel_frame stretch horizontally
    master_frame.columnconfigure(2,weight=100)  # let notes stretch horizontally
    
    master_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)


    def update_data(force_refresh=False):
        """Update the sparkline and value display for all channels.
        Should be called periodically (about 10/second) for smooth display.
        
        Only updates if the length of daq.data() has changed
        (unless force_refresh is set).
        """
        # freeze the count so that all sparklines stay synchronized
        freeze_count = len(daq.data())
        
        if daq.trigger_error:
            errorlabel['text']= 'Warning: '+daq.trigger_error
            errorlabel.grid(row=0, column=0)
        elif freeze_count \
            and freeze_count > daq.data_length_before_go \
                and daq.is_timed_trigger():
            # check for dropped packets in time stream
            implied_packets = daq.data_length_before_go \
                + int(daq.data()[freeze_count-1][0]/ daq.conf[0].period  +1.1)
#            print("DEBUG: implied_packets=",implied_packets, "freeze_count=", freeze_count, file=sys.stderr)
            if implied_packets>freeze_count:
                errorlabel['text'] = "Warning: {} packets dropped".format(implied_packets - freeze_count)
                errorlabel.grid(row=0, column=0)
            else:
                errorlabel.grid_forget()
        else:
            errorlabel.grid_forget()
        
        if force_refresh or freeze_count>int(countlabel['text']):
            for n, ch in enumerate(ChannelWidget.byloc, 1):
                ch.make_sparkline(n,freeze_count)
        countlabel['text'] = freeze_count
        if not force_refresh:
            root.after(100, update_data)
    
    root.update_idletasks()
#    root.resizable(False, False)
    root.tk.createcommand('scrollcan', scrollcan)
    root.bind_all('<MouseWheel>', 'scrollcan %D')
    
    # handle quits caused by deleting the window
    root.protocol('WM_DELETE_WINDOW', on_closing)
    
    #handle quits caused by keyboard shortcut
    root.createcommand('exit',on_closing)
    
    # On Macs, allow the dock icon to deiconify.
    root.createcommand('::tk::mac::ReopenApplication',root.deiconify)
    
    # On Macs, set up menu bar to be minimal.
    root.option_add('*tearOff', False)
    windowingsystem = root.tk.call('tk', 'windowingsystem')
    menubar = tk.Menu(root)
    if windowingsystem == 'aqua':
        appmenu = tk.Menu(menubar, name='apple')
        menubar.add_cascade(menu=appmenu)
    root['menu'] = menubar

    # Run update_data after 100 ms
    root.after(100, update_data)

root = tk.Tk()
daq = core.DataAcquisition()

ps = PortSelect(root, doconn)

root.mainloop()
