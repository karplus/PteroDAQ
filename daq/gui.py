from __future__ import division, print_function

import os.path
import sys
from itertools import chain
from math import sqrt,log
from functools import partial

try:
    import tkinter as tk
    from tkinter import messagebox as tkm
    from tkinter import filedialog as tkf
    from tkinter import ttk
    from tkinter import font as tkfont
except ImportError:
    import Tkinter as tk
    import tkMessageBox as tkm
    import tkFileDialog as tkf
    import tkFont as tkfont
    try:
        import ttk
    except ImportError:
        import ttkcompat as ttk # Python 2.6   
import core
from getports import ports
from comm import tostr
from newtext import create_newtext
from tkversionpatch import tk_patch_if_needed

# global variables:
#       root - the root of the Tkinter windowing
#       daq - the DataAcquisition object from core
#       maindir - the main directory containing the daq folder
#       os_background_color - background color for frames
#       master_frame - the Frame that holds all the GUI interface
#
# globals that could be local:
#       ps      the PortSelect object



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

def engineering_format(f,width=None,decimals=5):
    """Convert floating-point number to string using 'engineering' format,
    which is like the standard scientific format %<width>.<decimals>e,
    except that exponents are limited to multiples of three.
    """
    scientific = '{0:e}'.format(f)
    e_at = scientific.find('e')
    if e_at<0: 
        exponent=0
    else:
        exponent = int(scientific[e_at+1:])
    shift_right = exponent%3
    new_exponent = exponent-shift_right
    adjusted_f = f/10**new_exponent
    after_decimals = str(decimals-shift_right)
    if new_exponent==0:
        format_string = '{0:.' + after_decimals + 'f}'
        combined= format_string.format(adjusted_f)
    else:
        format_string = '{0:.' + after_decimals + 'f}e{1:+03d}'
        combined= format_string.format(adjusted_f,new_exponent)
    if width and len(combined)<width: 
        combined = ' '*(width-len(combined)) + combined
    return combined

class CommandBar(ttk.Frame):
    """Widget for the command buttons.
    """
    def __init__(self,master):
        ttk.Frame.__init__(self, master)

        self.last_file_saved=None
        
        # cache objects that we need access to for the commands
        
        ## define objects in commandbar Frame
        self.statelabel = ttk.Label(self, text='Paused', font=('TkTextFont', 0, 'bold'), width=12, anchor='center')
        self.countlabel = ttk.Label(self, text='0')
        
        recbutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/record.gif'), command=self.startrec)
        pausebutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/pause.gif'), command=self.pauserec)
        addchbutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/plus.gif'), command=self.newchannel)
        singlebutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/one.gif'), command=self.oneread)
        clearbutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/trash.gif'), command=self.ask_clear_reads)
        savebutton = ttk.Button(self, command=self.savefile, text='Save')
        
        reclabel = ttk.Label(self, text='Record')
        pauselabel = ttk.Label(self, text='Pause')
        addchlabel = ttk.Label(self, text='Add Channel')
        singlelabel = ttk.Label(self, text='Trigger Once')
        clearlabel = ttk.Label(self, text='Clear Data')

        ## grid items in commandbar frame
        self.statelabel.grid(row=0, column=2)
        self.countlabel.grid(row=1, column=2)
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
    
    def startrec(self,event=None):
        """Action to take when "Record" butting is pressed
        """
        if self.statelabel['text'] == 'Recording':
            # Don't restart if already recording.
            # This is questionable---restarting to get a new 0 time point
            # might be useful in marking human-observable events
            return
        config = self.makeconf()
        if config is None:
            return
        self.statelabel['text'] = 'Recording'
        root.title('PteroDAQ - Recording')
        master_frame.errorlabel.grid_forget()
        daq.config(config)
        if daq.is_timed_trigger():
            master_frame.triggers.set_period(daq.conf[0].period)
        daq.go()
    
    def pauserec(self,event=None):
        """Action to take when "Pause" button is pressed
        """
        daq.stop()
        self.statelabel['text'] = 'Paused'
        root.title('PteroDAQ - Paused')
        master_frame.other_global_options.powerlabel['text'] = master_frame.other_global_options.power_voltage_str()

    def oneread(self,event=None):
        """Configure the daq and do one read.
        """
        config = self.makeconf()
        if config is None:
            return
        daq.config(config)
        if daq.is_timed_trigger():
            master_frame.triggers.set_period(daq.conf[0].period)
        daq.oneread()

    def newchannel(self,event=None):
        if not self.ask_clear_reads():
            # BUG: errorlabel is cleared too soon for this report to work.
            # master_frame.errorlabel['text']="Can't add new channel until data cleared"
            # master_frame.errorlabel.grid(row=0,column=0)
            return
        ch = ChannelWidget(master_frame.inner_channel_frame)
        ch.pack(expand=True, fill='x')

        ch.update_idletasks()
        master_frame.update_channels()
        master_frame.channel_canvas.update_idletasks()
        master_frame.channel_canvas.yview_moveto(1)
    
    def clear_reads(self):
        """clear all recorded data and sparklines"""
        self.pauserec()
        daq.clear()
        for ch in master_frame.channel_list():
            ch.clear()
        self.countlabel['text'] = '0'
    
    def ask_clear_reads(self,event=None):
        """ask user whether to clear all reads, returns True if reads cleared"""
        if not daq.data(): return True
        if tkm.askyesno(message='Clear all {0} readings?'.format(len(daq.data())),
                icon='question', 
                parent=master_frame):
            self.clear_reads()
            return True
        return False
    
    def savefile(self,event=None):
        """Asks if you want to save file, using last_file_saved
        as a suggestion.
        returns either filename saved into, or None (if save cancelled)
        """
#        print("DEBUG: saving", len(daq.data()), "reads, last=", daq.data()[-1],file=sys.stderr)
        self.pauserec()
        config = self.makeconf()
        if config is None:
            return
        if self.last_file_saved:
            dir,file_base = os.path.split(self.last_file_saved)
            self.last_file_saved = tkf.asksaveasfilename(defaultextension='.txt',
                initialfile=file_base, initialdir=dir)
        else:
            self.last_file_saved = tkf.asksaveasfilename(defaultextension='.txt')
        if self.last_file_saved:
            daq.save(self.last_file_saved, notes=master_frame.notesbox.get('1.0', 'end'), 
                convvolts = master_frame.other_global_options.use_power_voltage.get(),
                new_conf=config
                )
        return self.last_file_saved
    
    def makeconf(self):
        """Constructs a tuple for passing to DataAcquistion.config()
        consisting of (trigger, aref, avg, channel descriptors)
        
        returns None if the time trigger is not parseable
        
        """
        trigger = master_frame.triggers.trigger_configuration()
        aref = daq.board.default_aref
        avg = master_frame.other_global_options.avgvar.get()
        channel_info =  [ ch.get_descriptor() for ch in master_frame.channel_list()]
        return (trigger, aref, avg, channel_info)
    

    
class TriggerOptions(ttk.Frame):
    """Widget for setting the triggering options.
    """
    def __init__(self,master):
        ttk.Frame.__init__(self, master)
        
        ## trigger options:
        self.triggertype = tk.IntVar()
        self.secvar = tk.DoubleVar()
        self.hzvar = tk.DoubleVar()
        self.pinvar = tk.StringVar(value=daq.board.eint[0][0])
        self.edgevar = tk.StringVar(value=daq.board.intsense[0][0])
        
        ## trace secvar and hzvar, so that they can be kept in sync
        self.secvar.trace('w', self.changetime)
        self.hzvar.trace('w', self.changetime)
        self.change_running=False
                # self.change_running is to prevent infinite recursion in changetime
                # Only make a change when self.change_running is False.
        
        ## set default values
        self.set_period(0.1)
        
        ## items for triggers widget        
        triggerlabel = ttk.Label(self, text='Trigger', font=('TkTextFont', 0, 'bold'))
        timetrigger = ttk.Radiobutton(self, text='Timed', variable=self.triggertype, value=0)
        pintrigger = ttk.Radiobutton(self, text='Pin Change', variable=self.triggertype, value=1)
        seclabel = ttk.Label(self, text='sec')
        hzlabel = ttk.Label(self, text='Hz')
        secfield = ttk.Entry(self, textvariable=self.secvar, width=12)
        hzfield = ttk.Entry(self, textvariable=self.hzvar, width=11)
        pinfield = ttk.Combobox(self, textvariable=self.pinvar, values=[x[0] for x in daq.board.eint])
        edgefield = ttk.Combobox(self, textvariable=self.edgevar, values=[x[0] for x in daq.board.intsense])
        pinfield['width'] = 8
        edgefield['width'] = 8

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
        
    def changetime(self,varname, varind, acc):
        """Update the seconds or hertz field when the other one is changed.
        The arguments are those provided by the "trace" method of a tk.DoubleVar:
            varname             the name of the variable
            varind              the array index into varname (empty string)
            acc         the operation being performed ('w')
        """
        if self.change_running:
            self.change_running = False
            return
        # print("DEBUG: changevar called with",repr(varname), repr(varind), repr(acc), file=sys.stderr)
        if varname == str(self.secvar):
            try:
                s = self.secvar.get()
                if s == 0:
                    return
                self.change_running = True
                self.hzvar.set(engineering_format(1/s,decimals=5))
            except ValueError:
                pass
        else:
            try:
                h = self.hzvar.get()
                if h == 0:
                    return
                self.change_running = True
                self.secvar.set(engineering_format(1/h,decimals=6))
            except ValueError:
                pass
    
    def trigger_configuration(self):
        """return trigger configuration suitable for passing to core configuration routine
        """
        if self.triggertype.get() == 0:
            try: 
                sec = self.secvar.get()
                if sec <=0:
                    raise ValueError('Period must be >0, not {}'.format(sec))
                return core.TriggerTimed(sec)
            except ValueError as err:
                print(err, file=sys.stderr)
                try:
                    hz = self.hzvar.get()
                    if hz <=0:
                        raise ValueError('Frequency must be >0, not {}'.format(hz))
                    return core.TriggerTimed(1./hz)
                except ValueError as errhz:
                    print(errhz, file=sys.stderr)
                    return None
        else:
#            print("DEBUG: trigger configuration for",self.pinvar.get(), self.edgevar.get(), "is", core.TriggerPinchange(self.pinvar.get(), self.edgevar.get()), file=sys.stderr)
            return core.TriggerPinchange(self.pinvar.get(), self.edgevar.get())
        
    def set_period(self,period):
        """ set the seconds to a known value 
                (either a default value or a computed actual value)
        """
        self.secvar.set(engineering_format(period,decimals=6))   

class OtherGlobalOptions(ttk.Frame):
    """Widget for setting the other global options.
    """
    def __init__(self,master):
        ttk.Frame.__init__(self, master)

        # items for other_global_options
        self.use_power_voltage = tk.BooleanVar(value=True)    # use power voltage for scaling
        self.avgvar = tk.StringVar()
        self.powerlabel = ttk.Checkbutton(self, text=self.power_voltage_str(), variable=self.use_power_voltage)

        if len(daq.board.avg) > 1:
            self.avglabel = ttk.Label(self, text='x Averaging')
            avgfield = ttk.OptionMenu(self, self.avgvar,  daq.board.default_avg, *(x[0] for x in daq.board.avg))
            avgfield['width'] = 5
        # grid items in other_global_options
            avgfield.grid(row=1, column=0, sticky='e')
            self.avglabel.grid(row=1, column=1, sticky='w')

        self.powerlabel.grid(row=0, column=0, columnspan=2)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def power_voltage_str(self):
        """return measured power voltage as a string
        """
        return 'Supply voltage: {0:.4f}'.format(daq.board.power_voltage)

class ImageButton(ttk.Label):
    """A button consisting of an image.
    Has no border except for that provided by the image.
    """
    def __init__(self, master, filename, command=None):
        img = tk.PhotoImage(file=filename)
        ttk.Label.__init__(self, master, image=img)
        self.img = img
        if command is not None:
            self.bind('<ButtonRelease-1>', command)

class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides automatically.
    """
    def set(self, low, high):
        if float(low) <= 0 and float(high) >= 1:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, low, high)

class PinChoiceMenu(tk.Menu):
    """Makes a menu for choosing pins.
    Generally only one such menu is made, shared by all ChannelWidgets.
    """
    sineimg=None
    squareimg=None
    
    def __init__(self,master,pinvar):
        """Construct PinChoiceMenu with two arguments:
                * the owner of the Menu (usually a MenuButton, whose image can be changed)
                * the tk.StringVar to change with this menu
        """
        tk.Menu.__init__(self,master,tearoff=False)
        if PinChoiceMenu.sineimg is None:
            PinChoiceMenu.sineimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/sinewave.gif'))
            PinChoiceMenu.squareimg = tk.PhotoImage(file=os.path.join(maindir, 'daq/icons/squarewave.gif'))

        self.pinvar = pinvar
        self.master = master
        
        if daq.board.analogs:
            analog_menu=tk.Menu(self)
            self.add_cascade(label='Analog',image=self.sineimg,menu=analog_menu,compound='left')
            for x in daq.board.analogs:
                analog_menu.add_command(label=x[0],  command=partial(self.set_pin, x[0]))
        if daq.board.differentials:            
            differential_menu=tk.Menu(self)
            self.add_cascade(label='Differential',image=self.sineimg,menu=differential_menu,compound='left')
            for x in daq.board.differentials:
                differential_menu.add_command(label=x[0],  command=partial(self.set_pin, x[0]))
        if daq.board.digitals:            
            digital_menu=tk.Menu(self)
            self.add_cascade(label='Digital',image=self.squareimg,menu=digital_menu, compound='left')
            for x in daq.board.digitals:
                if not daq.board.is_analog(x[0]):
                    digital_menu.add_command(label=x[0],  command=partial(self.set_pin, x[0]))
        if daq.board.frequencies:
            self.f_menu=tk.Menu(self,postcommand=self.build_frequency_menu)
            self.add_cascade(label='Frequency',image=self.squareimg,menu=self.f_menu, compound='left')
    
    def set_pin(self,pinname):
        """Set the pin variable to the named pin, and update the master's icon
        """
        self.pinvar.set(pinname)
#        print("DEBUG: setting pin to", pinname, file=sys.stderr)
        if daq.board.is_analog(pinname):
            self.master['image'] = PinChoiceMenu.sineimg
        elif daq.board.is_digital(pinname):
            self.master['image'] = PinChoiceMenu.squareimg
        elif daq.board.is_frequency(pinname):
            self.master['image'] = PinChoiceMenu.squareimg     # BUG: new icon needed
        else:
            self.master['image'] = None
        
    def build_frequency_menu(self):
        """Build a new frequency menu, greying out any unavailable frequency pins.
        """
        # clear out the existing menu
        self.f_menu.delete(0, 'end')

        # figure out which pins are on OTHER channels
        pinnames_in_use = set(ch.pinvar.get() for ch in master_frame.channel_list())
        current_pinname = self.pinvar.get()
        pinnames_in_use.remove(current_pinname)

        separator=None
        for freq_group in daq.board.frequencies:
            freq_set = set(f[0] for f in freq_group)
            if separator is not None:
                self.f_menu.add_separator()
            state = 'disabled' if freq_set & pinnames_in_use else 'normal'
            for x in freq_group:
                self.f_menu.add_command(label=x[0],  command=partial(self.set_pin, x[0]),
                        state=state)
            separator=True
    

class ChannelWidget(ttk.Frame):
    chnums = set([0])   # set of indices of all channels that haven't been removed
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        
        self.downsamp = 1
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label='Downsample', command=self.req_downsample)
        self.menu.add_command(label='Move Up', command=self.move_up)
        self.menu.add_command(label='Move Down', command=self.move_down)
        self.menu.add_command(label='Remove', command=self.remove)
        
        self.num = max(ChannelWidget.chnums) + 1
        ChannelWidget.chnums.add(self.num)
        
        # name of channel
        self.namevar = nv = tk.StringVar(value='ch{0}'.format(self.num))
        namefield = ttk.Entry(self, textvariable=nv, width=16, font=('TkTextFont', 0, 'bold'))
        namefield.focus()
        
        # which probe to use
        pinnames_in_use = set(ch.pinvar.get() for ch in master_frame.channel_list())
        try: 
            pin_for_default = next(x[0] for x in daq.board.analogs if x[0] not in pinnames_in_use)
        except StopIteration:
            pin_for_default = daq.board.analogs[0][0]
        self.pinvar = tk.StringVar(value=pin_for_default)
        pinchoice = ttk.Menubutton(self, textvariable=self.pinvar)
        pintype_menu = PinChoiceMenu(pinchoice,self.pinvar)
        pinchoice.configure(menu=pintype_menu)
        pinchoice['compound'] = 'left'
        #pinchoice['bg']=os_background_color
        
        # set default value for probe
        pinchoice['image'] = PinChoiceMenu.sineimg        
        
        # options button
        optbutton = ImageButton(self, filename=os.path.join(maindir, 'daq/icons/options.gif'), command=self.show_options)
        
        # canvas for sparkline
        self.sparkline_canvas = tk.Canvas(self, height=50, width=200, highlightthickness=0, 
                        bg='white')
        self.sparkline = self.sparkline_canvas.create_line(-2, -2, -2, -2) # out of sight, unlike (0, 0)

#        self.display_font = tkfont.Font(family="Courier",size=11)
        self.display_font= tkfont.Font(family='TkTextFont')
        
        width_in_chars = int(0.999 + self.display_font.measure('RMS:')/self.display_font.measure('n'))
        self.average_label = ttk.Label(self,anchor='w',width=width_in_chars,font=self.display_font)

        width_in_chars=int(0.999 + self.display_font.measure('-123.45e-03')/self.display_font.measure('n'))
        self.display_value = ttk.Label(self,width=width_in_chars, anchor='e', font=self.display_font,justify='right')
        
        # 0th, 1st, and 2nd moment for computing mean and rms
        self.x0=0
        self.x1=0
        self.x2=0
        
        ## grid all the items
        namefield.grid(row=0, column=0, sticky='ew')
        self.columnconfigure(0, weight=1)       # let namefield stretch
        self.columnconfigure(3, minsize=10, weight=3)   # let sparkline stretch mode
        pinchoice.grid(row=0, column=1)
        optbutton.grid(row=0, column=2)
        self.sparkline_canvas.grid(row=0, column=3, sticky='nsew')
        self.average_label.grid(row=0,column=4,sticky='ns')
        self.average_label.lower()
        self.display_value.grid(row=0,column=5,sticky='ns')
        
        self.rowconfigure(0, weight=1)
        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=6,
                         sticky='ew', padx=2, pady=5)
        
        # allow drag-to-resize
        self.bind('<B1-Motion>', self.change_height)
        
        # allow scrolling
        for w in [self] + self.winfo_children():
            w.bindtags(('channelscroll',) + w.bindtags())

    def remove(self, e=None):
        if not master_frame.commandbar.ask_clear_reads():
            # BUG: errorlabel is cleared too soon for this report to work.
            # master_frame.errorlabel['text']="Can't remove channel until data cleared"
            # master_frame.errorlabel.grid(row=0,column=0)
            return
        ChannelWidget.chnums.discard(self.num)
        self.destroy()
        master_frame.update_channels()
    
    def get_descriptor(self):
        """ return the descriptor used by the core for intepreting this channel
        """
        pin_name = self.pinvar.get()
        self.descriptor = core.ChannelDescriptor(name=self.namevar.get(),
                    probe= daq.board.probe_from_name[pin_name],
                    interpretation=core.Interpretation(
                        is_analog= daq.board.is_analog(pin_name) or daq.board.is_differential(pin_name),
                        is_signed=daq.board.is_differential(pin_name),
                        is_frequency=daq.board.is_frequency(pin_name),
                        downsample=self.downsamp, 
                        gain=daq.board.gain_from_name[pin_name])
                    )
#        print("DEBUG: pin_name=", pin_name, "gain=", daq.board.gain_from_name[pin_name], file=sys.stderr)
        return self.descriptor
    
    def change_height(self, e):
        """Change the height of a ChannelWidget by an event
        (bound, for example, to <B1-Motion>)
        """
        self.sparkline_canvas['height'] = e.y
        self.update_idletasks()
        master_frame.update_channels()
    
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
        # make a copy of the data into visible_data, to transform in place
        start = max(0, freeze_count-width)
        visible_data = [x[chan_num] for x in daq.data()[start:freeze_count]]
#        print("DEBUG: len(visible_data)=",len(visible_data), file=sys.stderr)
        
        # update value at end of line
        self.average_label['text']='last:\nDC:\nRMS:'
        last_value = visible_data[-1]
        if self.x0 < 100:
            # zero out the old sums, to recompute from the beginning
            #   This is a crude, possibly buggy attempt to correct for
            #   frequency channels getting their first value patched
            self.x0 = 0
            self.x1 = 0
            self.x2 = 0
        self.x1 += sum(x[chan_num]    for x in daq.data()[self.x0:freeze_count])
        self.x2 += sum(x[chan_num]**2 for x in daq.data()[self.x0:freeze_count])
        self.x0 = freeze_count
        mean=self.x1/self.x0
        ms=max(0,self.x2/self.x0-mean**2)
        rms=sqrt(ms)
        if  self.descriptor.interpretation.is_analog and master_frame.other_global_options.use_power_voltage.get():
            last_value = self.descriptor.volts(last_value,daq.board.power_voltage)
            mean = self.descriptor.volts(mean,daq.board.power_voltage)
            rms = self.descriptor.volts(rms,daq.board.power_voltage)
            self.display_value['text']= '\n'.join([engineering_format(x,7,4) for x in (last_value,mean,rms)])
        elif self.descriptor.interpretation.is_frequency:
            self.display_value['text']= '\n'.join([engineering_format(x,7,4) for x in (last_value,mean,rms)])
        else:
            self.display_value['text']= '{0:7.0f}\n{1:7.4f}\n{2:7.4f}'.format(last_value,mean,rms)

        if len(visible_data)<2:
            return      # too short make a line
            
        # scale visible_data to 0..height-1 range
        # (more positive data is lower scaled value)
        if self.descriptor.interpretation.is_analog:
            if self.descriptor.interpretation.is_signed:
                for n,d in enumerate(visible_data):
                    visible_data[n] = (height-1)*(1.- (d+32768)/65536.)
            else:
                for n,d in enumerate(visible_data):
                    visible_data[n] = (height-1)*(1.- d/65536.)
        elif self.descriptor.interpretation.is_frequency:
            for n,d in enumerate(visible_data):
                visible_data[n] = (height-1)*(1- max(0, log(1+d)/16.))
        else:
            for n,d in enumerate(visible_data):
                visible_data[n] = (height-1)*(1- d)
        
        self.sparkline_canvas.coords(self.sparkline, 
             *(chain.from_iterable(enumerate(visible_data,width-len(visible_data)))))
    
    def clear(self):
        self.sparkline_canvas.coords(self.sparkline, -2, -2, -2, -2)
        self.x0=0
        self.x1=0
        self.x2=0
        self.display_value['text']=''
    def show_options(self, e):
        self.menu.post(e.x_root, e.y_root)
    def _adj_downsample(self, dv, win, e=None):
        try:
            val = dv.get()
        except ValueError:
            tkm.showwarning('Illegal Value', 'Not an integer.\nPlease try again')
            return
        if val < 1:
            tkm.showwarning('Too Small', 'The allowed minimum value is 1.\nPlease try again')
            return
        self.downsamp = val
        win.destroy()
    def req_downsample(self, e=None):
        win = tk.Toplevel(root)
        f = ttk.Frame(win)
        win.title('Downsampling')
        dv = tk.IntVar(value=self.downsamp)
        adj = partial(self._adj_downsample, dv, win)
        lbl = ttk.Label(f, text='Downsample channel {0} by'.format(self.namevar.get()))
        ent = ttk.Entry(f, textvariable=dv)
        ok = ttk.Button(f, text='OK', command=adj, default='active')
        cancel = ttk.Button(f, text='Cancel', command=win.destroy)
        ent.bind('<Return>', adj)
        f.grid(padx=10, pady=10)
        lbl.grid(row=0, column=0, columnspan=2)
        ent.grid(row=1, column=0, columnspan=2)
        ok.grid(row=2, column=0)
        cancel.grid(row=2, column=1)
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
    def move_up(self, e=None):
        channels = master_frame.channel_list()
        ind = channels.index(self)
        if ind == 0:
            return
        self.pack(before=channels[ind-1])
    def move_down(self, e=None):
        channels = master_frame.channel_list()
        ind = channels.index(self)
        if ind == len(channels)-1:
            return
        self.pack(after=channels[ind+1])

class PortSelect(object):
    def __init__(self, win, cb):
        self.win = win
        win.title('PteroDAQ - Select a Device')
        self.cb = cb
        self.port_frame = port_frame = ttk.Frame(win)
        self.pl = ttk.Treeview(port_frame, show='tree', selectmode='browse')
        self.pl.bind('<Return>', self.useport)
        self.updateports()
        self.go_btn = ttk.Button(port_frame, text='Go', command=self.useport, default='active')
        self.pl.grid(row=0, column=0, sticky='news')
        self.go_btn.grid(row=1,column=0, sticky='s')
        port_frame.columnconfigure(0,weight=1)
        port_frame.rowconfigure(0,weight=1)
        port_frame.pack(fill='both', expand='yes')

    def useport(self,*args):
        treeview_selections=self.pl.selection()
        if not treeview_selections:
            # nothing selected (probably no board plugged in)
            tkm.showerror('No board', 'No PteroDAQ board selected---plug one in and try again')
            return
        portname, port = self.ps[int(treeview_selections[0])]
        self.pl.after_cancel(self.aft)
        self.pl.destroy()
        self.go_btn.destroy()
        self.cb(tostr(port))
        self.conn_label = ttk.Label(self.port_frame, padding=10,
            text='Connecting to\n{0}\n{1}'.format(tostr(portname), tostr(port)))
        self.conn_label.pack()
        self.win.title('PteroDAQ - Connecting')
        self.aft = root.after(100, self.checkstart)
    def updateports(self):
        ps = self.ps = ports()
        portlist = self.pl
        fc = portlist.selection()
        #print('DEBUG: fc =', repr(fc), file=sys.stderr)
        #print('DEBUG: ps =', repr(ps), file=sys.stderr)
        if fc:
            fcn = portlist.item(int(fc[0]), 'text')
        elif ps:
            fcn = ps[0][0]
        else:
            fcn = None
        if isinstance(fcn, list): # python 3.4.3
            fcn = bytes(fcn)
        if isinstance(fcn, bytes):
            fcn = tostr(fcn)
        #print('DEBUG: fcn =', repr(fcn), file=sys.stderr)
        for x in portlist.get_children():
            portlist.delete(x)
        for n, x in enumerate(ps):
            nm = tostr(x[0])
            portlist.insert('', 'end', str(n), text=x[0])
            #print('DEBUG: nm =', repr(nm), file=sys.stderr)
            if nm == fcn:
                #print('DEBUG: n =', repr(n), file=sys.stderr)
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
                # completed successfully
                self.port_frame.destroy()
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


class MasterFrame(ttk.Frame):
    """Master window that contains all the input and output widgets.
    """
    def __init__(self,master):
        ttk.Frame.__init__(self, master)
        
        ## root:
        ##  MasterFrame
        ##      CommandBar commandbar
        ##      Frame global_options
        ##          TriggerOptions triggers
        ##          Frame other_global_options
        ##      Frame notes
        ##      Frame channel_frame
        ##        Canvas channel_canvas
        ##          Frame inner_channel_frame

        global_options = ttk.Frame(self)
        self.triggers = TriggerOptions(global_options)
        self.other_global_options= OtherGlobalOptions(global_options)
        
        notes = ttk.Frame(self)
        channel_frame = ttk.Frame(self)
        
        self.commandbar = CommandBar(self)	# defined last to ensure access to other parts of MasterFrame

        ##grid items in global_options
        self.triggers.grid(row=0,column=0,sticky='new')
        ttk.Separator(global_options, orient='horizontal').grid(row=1,column=0,sticky='ew')
        self.other_global_options.grid(row=2,column=0,sticky='sew')
        global_options.columnconfigure(0, weight=1)

        ## define items in notes frame
        self.errorlabel = ttk.Label(notes, text='Error: triggering too fast', foreground='red')
        noteslabel = ttk.Label(notes, text='Notes', font=('TkTextFont', 0, 'bold'))
        self.notesbox = tk.Text(notes, height=7, width=60, wrap='word', highlightthickness=0, font='TkTextFont', undo=True)
        notescroll = AutoScrollbar(notes, orient='vertical', command=self.notesbox.yview)
        self.notesbox['yscrollcommand'] = notescroll.set
        self.notesbox.bindtags(tuple('newtext' if x == 'Text' else x for x in self.notesbox.bindtags()))
#        print('DEBUG: notesbox.bindtags=', self.notesbox.bindtags(), file=sys.stderr)
#        print('DEBUG: notesbox.bind=', self.notesbox.bind(), file=sys.stderr)
#        print('DEBUG: root.bind_class("newtext")=', root.bind_class('newtext'), file=sys.stderr)
#        print('DEBUG: root.bind_class("newtext","<<SelectAll>>")=', root.bind_class('newtext','<<SelectAll>>'), file=sys.stderr)
#        print('DEBUG: root.event_info("<<SelectAll>>")=', root.event_info('<<SelectAll>>'), file=sys.stderr)
#        print('DEBUG: root.event_info("<<PrevChar>>")=', root.event_info('<<PrevChar>>'), file=sys.stderr)
        self.notesbox.mark_set('anchor', 'insert')

        ## grid items in notes frame
        noteslabel.grid(row=1, column=0)
        self.notesbox.grid(row=2, column=0, sticky='nsew')
        notescroll.grid(row=2, column=1, sticky='nse')
        notes.columnconfigure(0,weight=1)
        notes.rowconfigure(2,weight=1)

        ## define items for channel_frame
        self.channel_canvas = tk.Canvas(channel_frame,
                       background= os_background_color,
                       highlightthickness=0)
        self.inner_channel_frame = ttk.Frame(channel_frame)
        # inner_channel_frame must be after channel_canvas to layer on top
        self.inner_channel_window=self.channel_canvas.create_window(0, 0, anchor='nw', window=self.inner_channel_frame)
        self.channel_canvas.bind('<Configure>', self.inner_channel_change_width)
        channel_scrollbar = AutoScrollbar(channel_frame, orient='vertical', command=self.channel_canvas.yview)
        self.channel_canvas['yscrollcommand'] = channel_scrollbar.set

        ## grid items for channel_frame
        self.channel_canvas.grid(row=0, column=0, sticky='nsew')
        channel_scrollbar.grid(row=0, column=1, sticky='nse')
        channel_frame.columnconfigure(0, weight=1)
        channel_frame.rowconfigure(0, weight=1)

        ## grid items for master frame 
        self.commandbar.grid(row=0, column=0, columnspan=3, sticky='ew', padx=2, pady=2)
        ttk.Separator(self, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew')
        global_options.grid(row=2, column=0, sticky='ew')
        ttk.Separator(self, orient='vertical').grid(row=2, column=1, sticky='nsw')
        notes.grid(row=2, column=2, sticky='nsew')
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew')
        channel_frame.grid(row=4, column=0, columnspan=3, sticky='nsew')

        self.rowconfigure(4,weight=1)       # let channel_frame stretch vertically
        self.columnconfigure(0,weight=1)    # let commandbar and channel_frame stretch horizontally
        self.columnconfigure(2,weight=100)  # let notes stretch horizontally

        self.grid(row=0, column=0, sticky='nsew')
        root.columnconfigure(0,weight=1)
        root.rowconfigure(0,weight=1)
        
        root.bind_class('channelscroll', '<MouseWheel>', self.scrollcan)
        root.bind_class('channelscroll', '<Button-4>', self.scrollcan)
        root.bind_class('channelscroll', '<Button-5>', self.scrollcan)
    
    # Weird way to allow inner_channel_frame to resize to fill canvas
    def inner_channel_change_width(self,event):
        """Function to bind to '<Configure>' of a canvas to make it adjust its size
        when the window is resized.
        """
        self.channel_canvas.itemconfig(self.inner_channel_window, width = event.width)
        self.update_channels()

    def scrollcan(self, event):
        """Scroll the channel_canvas, based on an event from either a MouseWheel or Trackpad
        (Note: scrollbar handled automatically, not here.)
        """
        # delta is the movement to make in yview_scroll
#        print('DEBUG: event.type=',repr(event.type),'event.delta=',event.delta, file=sys.stderr)
        if int(event.type) == 38: # 'MouseWheel'
            delta = -int(event.delta)
        elif event.num == 4: # button 4 on X11
            delta = -1
        else:			# button 5 on X11
            delta = 1
        if delta >= 120 or delta <= -120:
            # On Windows, MouseWheel deltas are 120 times larger than on Mac
            delta /= 120
        self.channel_canvas.yview_scroll(int(delta), 'units')

    def on_closing(self):
        """Code to run when user attempts to close window
        """
        if daq.num_saved < len(daq.data()):
            save_before_quit=tkm.askyesnocancel(
                title='Unsaved readings',
                message='{0} unsaved readings\nSave before quitting?'.format(len(daq.data())),
                parent=self)
            if save_before_quit is None:
                # cancel returns None
                return
            if save_before_quit:
                if not self.commandbar.savefile():
                    return      # save dialog cancelled
        root.destroy()

    def channel_list(self):
        """return the ChannelWidgets in the inner_channel_frame
        """
        return self.inner_channel_frame.pack_slaves()
    
    def update_channels(self):
        """Update scroll region and sparklines after changing size of inner_channel_frame 
        """
        self.inner_channel_frame.update_idletasks()
        self.channel_canvas['scrollregion'] = (0,0,
                self.inner_channel_frame.winfo_width(), 
                self.inner_channel_frame.winfo_height())
        self.update_data(force_refresh=True)


    def update_data(self,force_refresh=False):
        """Update the sparkline and value display for all channels.
        Should be called periodically (about 10/second) for smooth display.
        
        Only updates if the length of daq.data() has changed
        (unless force_refresh is set).
        """
        # freeze the count so that all sparklines stay synchronized
        freeze_count = len(daq.data())
        
        if daq.trigger_error:
            self.errorlabel['text']= 'Warning: '+daq.trigger_error
            self.errorlabel.grid(row=0, column=0)
        elif freeze_count \
            and freeze_count > daq.data_length_before_go \
                and daq.is_timed_trigger():
            # check for dropped packets in time stream
            implied_packets = daq.data_length_before_go \
                + int(daq.data()[freeze_count-1][0]/ daq.conf[0].period  +1.1)
#            print("DEBUG: implied_packets=",implied_packets, "freeze_count=", freeze_count, file=sys.stderr)
            if implied_packets>freeze_count:
                self.errorlabel['text'] = 'Warning: {0} samples dropped'.format(implied_packets - freeze_count)
                self.errorlabel.grid(row=0, column=0)
            else:
                self.errorlabel.grid_forget()
        else:
            self.errorlabel.grid_forget()
        
        if force_refresh or freeze_count>int(self.commandbar.countlabel['text']):
            for n, ch in enumerate(self.channel_list(), 1):
                ch.make_sparkline(n,freeze_count)
        self.commandbar.countlabel['text'] = freeze_count
        if not force_refresh:
            root.after(100, self.update_data)

def main(e=None):
    global master_frame
    global os_background_color
        
    try:
        # on Mac OS X, the background color for windows has a strange name
        # not supported on other platforms.
        root.winfo_rgb('systemSheetBackground')
        os_background_color = 'systemSheetBackground'
    except tk.TclError:
        # on other platforms the background is set already
        os_background_color = root['bg']
    
    master_frame = MasterFrame(root)
    root.title('PteroDAQ - Paused')
    root.geometry('650x450')
    
    root.update_idletasks()
        
    # handle quits caused by deleting the window
    root.protocol('WM_DELETE_WINDOW', master_frame.on_closing)
    
    # handle quits caused by keyboard shortcut
    root.createcommand('exit', master_frame.on_closing)
    
    # Run update_data after 100 ms
    root.after(100, master_frame.update_data)

def create_root():
    """Creates the top-level root object for Tkinter
    and initializes various properties, 
    mainly dealing with top-level menus and icons
    """
    root = tk.Tk()
    
    tk_patch_if_needed(root)
    create_newtext(root)
    
    # On Macs, allow the dock icon to deiconify.
    root.createcommand('::tk::mac::ReopenApplication', root.deiconify)
    
    # On Macs, set up menu bar to be minimal.
    root.option_add('*tearOff', False)
    windowingsystem = root.tk.call('tk', 'windowingsystem')
    menubar = tk.Menu(root)
    if windowingsystem == 'aqua':
        appmenu = tk.Menu(menubar, name='apple')
        menubar.add_cascade(menu=appmenu)
    root['menu'] = menubar
    
    # On Linux and Windows, set the app's icon
    appicon = tk.PhotoImage(file=os.path.join(maindir, 'extras/appicons/pterodaq512.gif'))
    root.tk.call('wm', 'iconphoto', root._w, appicon)
    
    root.geometry('280x200')
    root.lift()
    root.focus_force()
    
    return root

daq = core.DataAcquisition()

root = create_root()

ps = PortSelect(root, partial(daq.connect, call_when_done=startmain))

root.mainloop()
