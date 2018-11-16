from __future__ import division,print_function
import sys
from struct import unpack_from


def limit(x, a, b):
    x = int(x)
    if x < a:
        return a
    if x > b:
        return b
    return x

class Board(object):
    """Abstract base class for all board descriptions
    """
    # class-level variables:
    by_id ={}   # maps model numbers to board descriptions,
                # which are subclasses of Board
    
    # members of classes:
    names=()    # tuple of names of boards fitting this description
                # (currently just documentation)
    bandgap = None      # nominal bandgap voltage 
                        # connected to ADC input channel for specific board

    analogs=()  # tuple of pairs (analog pin name, channel number)
    digitals=() # tuple of pairs (digital pin name, port and position code)
    differentials=()    # tuple of either pairs ("X-Y", channel number)
                        # or 5-tuples ("g*(X-Y)", channel number, "X","Y", gain)
    frequencies=()      # tuple of tuple of pairs, 
                        #       each top-level being one port
                        #       each pair being one pin of the port ("D0", channel_number)
    
    eint = ()   # tuple of pairs (interrupt pin name, interrupt number)
    
    aref = ()   # tuple of pairs (analog reference name, code from data sheet)
    default_aref = None # what analog reference name to use by default
    
    intsense = ()       # tuple of pairs
                        # (triggering type name, numeric code)
                        # 'rises', 'falls', 'changes'
                        # Ordered for human interface.
    
    avg = (('1',1),)    # tuple of pairs
                        # hardware averaging options for board
                        # (name of option, numeric code)
    
    default_avg = '1'   # default averaging is to use none (averaging 1 sample)
                        # but can be overridden in specific boards
    
    
    # Some of these should probably be instance variables rather than class variables.
    # We've been sloppy about this, because we assume only one board ever instantiated.
    power_voltage = None # power supply voltage, needed for analog reference info
    
    frequency_dead_cycles = 0   # how many cycles is frequency counter turned off for
        # on each sample.

    def __init__(self):
        """Build dict self.name_from_probe, mapping probes to names.
        Build dict self.probe_from_name, mapping names to probes.
        """
        self.timestamp_res = None # resolution of timestamps in seconds
        self.name_from_probe=dict()
        self.probe_from_name=dict()
        self.gain_from_name=dict()
        for name,pin in self.digitals:
            probe = 2 | (pin << 8)
            self.name_from_probe[probe]=name
            self.probe_from_name[name]=probe
            self.gain_from_name[name]=1

        for name,mux in self.analogs:
            probe = 1 | (mux << 8)
            self.name_from_probe[probe]=name
            self.probe_from_name[name]=probe
            self.gain_from_name[name]=1

        for flist in self.frequencies:
            for name,mux in flist:
                probe = 3 | (mux << 8)
                self.name_from_probe[probe]=name
                self.probe_from_name[name]=probe
                self.gain_from_name[name]=1

        for diff in self.differentials:
            name = diff[0]
            mux = diff[1]
            probe = 1 | (mux << 8)
            self.name_from_probe[probe]=name
            self.probe_from_name[name]=probe
            self.gain_from_name[name]=0.5 if len(diff)<5 else 0.5*diff[-1]
    
    def is_differential(self,name):
        """Is this the name for a differential channel?"""
        return name in (x[0] for x in self.differentials)
    
    def is_analog(self,name):
        """Is this the name for a single-ended analog channel?"""
        return name in (x[0] for x in self.analogs)
    
    def is_frequency(self,name):
        """Is this the name for a frequency channel?"""
        return name in (x[0] for f in self.frequencies for x in f )
    
    def is_digital(self,name):
        """Is this the name for a digital channel?"""
        return name in (x[0] for x in self.digitals)
    
    def setup(self, model):
        """unpacks model information sent from model info command
            and updates parameters for power_voltage and timing
        """       
        m = unpack_from('<HL', model, offset=0)
#        print("DEBUG: m=", m, "self.bandgap=", self.bandgap, file=sys.stderr)
        self.power_voltage = 65536./(m[0]/self.bandgap) # left aligned to 16 bits (even if only 10 bits)
        self._tmr_base = 1./(m[1]*1000) # frequency given in kHz
#        print("Frequency ", m[1])
        self.timestamp_res = self._tmr_base* self.CPU_clocks_per_tick
         
        # how much time, in seconds is frequency counter turned off for
        # on each sample.  If the count during the dead time is greater than 1, then
        # counts will be missed.
        self.frequency_dead_time = self.frequency_dead_cycles * self._tmr_base

    @classmethod
    def supported(cls, model_num):
        """class decorator for appending subclasses to 
        Board's dictionary of supported boards
        """
        def decorator(brd):
            cls.by_id[model_num]=brd
            return brd
        return decorator
     
    def _latex_columns(board):
        """returns the names and values of the columns of the latex table
        """
        return ( ("Board names", board.names)
                ,      ("analog", len(board.analogs))
                ,      ("differential", len(board.differentials))
                ,      ("digital", len(board.digitals))
                ,      ("frequency", len(board.frequencies))
                ,      ("trigger", len(board.eint))
                )           
     
    def _print_latex_row(board):
         """print one row of a LaTeX table describing this board
         Intended for use from Board.print_latex_table only.
         """
         cols = Board._latex_columns(board)
         bnames = cols[0][1]
         print("\\begin{tabular}{l}")
         print("\\rule{0em}{3ex}%")
         for name in bnames:
              print(name, "\\\\")
         print("[0.8ex]")
         print("\\end{tabular} &")
         
         for col_name,col_value in cols[1:-1]:
              print ( col_value, "&")
         print (cols[-1][1], "\\\\")
         print ( "\\hline" )
     
    def print_latex_table():
        """Print a LaTeX table listing all the boards
        """
        board1=Board.by_id[1]
        cols = Board._latex_columns(board1)
        print("\\begin{tabular}[c]{l|", "c"*(len(cols)-1), "}")
        print("& \\multicolumn{", len(cols)-1, "}{c}{channels}\\\\")
        for col_name,col_value in cols[:-1]:
                print ( col_name, "&", end="")
        print(cols[-1][0], "\\\\")
        print("\\hline")
        for id in range(1,len(Board.by_id)+1):
            Board._print_latex_row(Board.by_id[id])
        print("\\end{tabular}")

        
class ArduinoAVR(Board):
    """Board description abstract class for Arduino boards
    and compatibles using AVR processors
    """
    
    CPU_clocks_per_tick = 8
    intsense = (
        ('rises', 3),
        ('falls', 2),
        ('changes', 1),
        #('is low', 0)
        # removed due to lack of rate-limiting causing hang
        )
    avg = (
        ('1', 1),)
    bandgap = 1.1
    default_timestamp_res = 0.5e-6 # half-microsecond
    
    def timer_calc(self, period):
        """computes counter parameters
                n is index for prescaler
                top is counter period in prescaled ticks
                actual time in seconds
            returns (actual, (n,top))
        """
        # using Timer1
        prescales = (1, 8, 64, 256, 1024)
        base = self._tmr_base
        for n, pr in enumerate(prescales, 1):
            if period <= ((1<<16) - 2) * pr * base:
                break
        top = limit(round(period / (pr * base)), 3, (1<<16)-1)
        actual = (pr * top * base)
        return actual, (n, top)


@Board.supported(1)
class ArduinoStandard(ArduinoAVR):
    names = (
        'Arduino Uno',
        'Arduino Duemilanove',
        'Arduino Diecimila',
        'Arduino Ethernet',
        'Arduino Pro',
        'Arduino LilyPad')
    analogs = (
        ('A0', 0),
        ('A1', 1),
        ('A2', 2),
        ('A3', 3),
        ('A4', 4),
        ('A5', 5),
        ('Temperature', 8),
        ('Bandgap', 14))
    digitals = (
        ('D0', 48),
        ('D1', 49),
        ('D2', 50),
        ('D3', 51),
        ('D4', 52),
        ('D5', 53),
        ('D6', 54),
        ('D7', 55),
        ('D8', 16),
        ('D9', 17),
        ('D10', 18),
        ('D11', 19),
        ('D12', 20),
        ('D13', 21),
        ('A0', 32),
        ('A1', 33),
        ('A2', 34),
        ('A3', 35),
        ('A4', 36),
        ('A5', 37))
    eint = (
        ('D2', 0),
        ('D3', 1))
    default_aref = 'Power'
    aref = (
        ('Power', 1),
        ('AREF', 0),
        ('1.1V', 3))

@Board.supported(2)
class ArduinoExtraAnalog(ArduinoStandard):
    names = (
        'Arduino Mini',
        'Arduino Nano',
        'Arduino Pro Mini',
        'Arduino Fio')
    analogs = (
        ('A0', 0),
        ('A1', 1),
        ('A2', 2),
        ('A3', 3),
        ('A4', 4),
        ('A5', 5),
        ('A6', 6),
        ('A7', 7),
        ('Temperature', 8),
        ('Bandgap', 14))

@Board.supported(3)
class ArduinoMega(ArduinoAVR):
    names = ('Arduino Mega',)
    analogs = (
        ('A0', 0),
        ('A1', 1),
        ('A2', 2),
        ('A3', 3),
        ('A4', 4),
        ('A5', 5),
        ('A6', 6),
        ('A7', 7),
        ('A8', 32),
        ('A9', 33),
        ('A10', 34),
        ('A11', 35),
        ('A12', 36),
        ('A13', 37),
        ('A14', 38),
        ('A15', 39),
        ('Bandgap', 30))
    digitals = (
        ('D0', 64),
        ('D1', 65),
        ('D2', 68),
        ('D3', 69),
        ('D4', 101),
        ('D5', 67),
        ('D6', 115),
        ('D7', 116),
        ('D8', 117),
        ('D9', 118),
        ('D10', 20),
        ('D11', 21),
        ('D12', 22),
        ('D13', 23)) # To Do: finish listing Mega digitals
    eint = (
        ('D2', 4),
        ('D3', 5),
        ('D18', 3),
        ('D19', 2),
        ('D20', 1),
        ('D21', 0))
    default_aref = 'Power'
    aref = (
        ('Power', 1),
        ('AREF', 0),
        ('1.1V', 2),
        ('2.56V', 3))

@Board.supported(4)
class Arduino32u4(ArduinoAVR):
    names = (
        'Arduino Leonardo',
        'Arduino Yun',
        'Arduino Micro',
        'Arduino Robot',
        'Arduino Esplora',
        'Arduino LilyPad USB')
    analogs = (
        ('A0', 7),
        ('A1', 6),
        ('A2', 5),
        ('A3', 4),
        ('A4', 1),
        ('A5', 0),
        ('A6/D4', 32),
        ('A7/D12', 33),
        ('A8/D6', 34),
        ('A9/D8', 35),
        ('A10/D9', 36),
        ('A11/D10', 37),
        ('Temperature', 39),
        ('Bandgap', 30))
    digitals = (
        ('D0', 50),
        ('D1', 51),
        ('D2', 49),
        ('D3', 48),
        ('D4', 52),
        ('D5', 38),
        ('D6', 55),
        ('D7', 70),
        ('D8', 20),
        ('D9', 21),
        ('D10', 22),
        ('D11', 23),
        ('D12', 54),
        ('D13', 39),
        ('A0', 87),
        ('A1', 86),
        ('A2', 85),
        ('A3', 84),
        ('A4', 81),
        ('A5', 80),
        ('SCK', 17),
        ('MOSI', 18),
        ('MISO', 19))
    differentials= ()
    
    # it turns out that the "differential" ADC is complete
    # crap on the 32U4 chip.  The ADLAR shift doesn't get the 
    # low-resolution difference into the right position,
    # and the 10x amplifier seems to randomly flip the sign of
    # the amplification from time to time.
    # We will NOT be implementing differential channels on Leonardo
    # boards for PteroDAQ!
    NON_WORKING_differentials= (
        ('A0-A4', 23, 'A0', 'A4', 1),
        ('A1-A4', 22, 'A1', 'A4', 1),
        ('A2-A4', 21, 'A2', 'A4', 1),
        ('A3-A4', 20, 'A3', 'A4', 1),
        ('10(A4-A5)', 9, 'A4', 'A5', 10),
        ('40(A4-A5)', 38, 'A4', 'A5', 40),
        ('200(A4-A5)', 11, 'A4', 'A5', 200),
        ('A5-A4', 16, 'A5', 'A4', 1),
        ('10(A3-A5)', 40, 'A3', 'A5', 10),
        ('10(A2-A5)', 41, 'A2', 'A5', 10),
        ('10(A1-A5)', 42, 'A1', 'A5', 10),
        ('10(A0-A5)', 43, 'A0', 'A5', 10),
        ('10(A3-A4)', 44, 'A3', 'A4', 10),
        ('10(A2-A4)', 45, 'A2', 'A4', 10),
        ('10(A1-A4)', 46, 'A1', 'A4', 10),
        ('10(A0-A4)', 47, 'A0', 'A4', 10),
        ('40(A3-A5)', 48, 'A3', 'A5', 40),
        ('40(A2-A5)', 49, 'A2', 'A5', 40),
        ('40(A1-A5)', 50, 'A1', 'A5', 40),
        ('40(A0-A5)', 51, 'A0', 'A5', 40),
        ('40(A3-A4)', 52, 'A3', 'A4', 40),
        ('40(A2-A4)', 53, 'A2', 'A4', 40),
        ('40(A1-A4)', 54, 'A1', 'A4', 40),
        ('40(A0-A4)', 55, 'A0', 'A4', 40),
        ('200(A3-A5)', 56, 'A3', 'A5', 200),
        ('200(A2-A5)', 57, 'A2', 'A5', 200),
        ('200(A1-A5)', 58, 'A1', 'A5', 200),
        ('200(A0-A5)', 59, 'A0', 'A5', 200),
        ('200(A3-A4)', 60, 'A3', 'A4', 200),
        ('200(A2-A4)', 61, 'A2', 'A4', 200),
        ('200(A1-A4)', 62, 'A1', 'A4', 200),
        ('200(A0-A4)', 63, 'A0', 'A4', 200))    
    eint = (
        ('D0', 2),
        ('D1', 3),
        ('D2', 1),
        ('D3', 0),
        ('D7', 6))
    default_aref = 'Power'
    aref = (
        ('Power', 1),
        ('AREF', 0),
        ('2.56V', 3))

@Board.supported(5)
class FreedomKL25(Board):
    names = ('FRDM-KL25Z',)
    CPU_clocks_per_tick = 2
    bandgap = 1.0
    analogs = (
        ('PTB0', 8),
        ('PTB1', 9),
        ('PTB2', 12),
        ('PTB3', 13),
        ('PTC0', 14),
        ('PTC1', 15),
        ('PTC2', 11),
        ('PTD1', 69),
        ('PTD5', 70),
        ('PTD6', 71),
        ('PTE20', 0),
        ('PTE21', 4),
        ('PTE22', 3),
        ('PTE23', 7),
        ('PTE29', 68),
        ('PTE30', 23),
        ('Temperature', 26),
        ('Bandgap', 27),
#        ('Aref', 29)
        )
         # To Do: internal differentials?
    digitals = tuple(('PT{0}{1}'.format(port[0], pin), (n * 32 + pin)) for n, port in enumerate((
            ('A', (1, 2, 4, 5, 12, 13, 14, 15, 16, 17)),
            ('B', (0, 1, 2, 3, 8, 9, 10, 11)),
            ('C', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17)),
            ('D', (0, 1, 2, 3, 4, 5, 6, 7)),
            ('E', (0, 1, 2, 3, 4, 5, 20, 21, 22, 23, 30, 31))
        )) for pin in port[1])
    differentials=(
        ('PTE20-PTE21', 32),
        ('PTE22-PTE23', 35))

    
    def make_eint(digitals,interrupt_ports):
        # This strange function is here because list comprehensions
        # ignore the class-scoped variables in Python3.
        return [d for d in digitals if (d[0][:3] in interrupt_ports)]
    eint=make_eint(digitals, ('PTA', 'PTD'))
    
    def make_frequencies(digitals,dma_ports):
        return [ [("f({0})".format(d[0]),d[1]) for d in digitals if d[0][:3]==port] for port in dma_ports ]
    frequencies=make_frequencies(digitals, ('PTA', 'PTD'))

    intsense = (
        ('rises', 1),
        ('falls', 2),
        ('changes', 3),
        #('is low', 0),
        #('is high', 4)
        # removed due to lack of rate-limiting causing hang
        )
    default_aref = 'Power'
    aref = (
        ('Power', 1),
        ('AREF', 0))
    avg = (
        ('1', 0),
        ('4', 4),
        ('8', 5),
        ('16', 6),
        ('32', 7))
    default_avg='4'
    
    frequency_dead_cycles = 48  # about 1usec dead time in frequency counter (BUG: number not checked)

    def timer_calc(self, period):
        """computes counter parameters
                n is index for prescaler
                reload is counter period-1 in prescaled ticks
                actual time in seconds
            returns (actual, (n,reload))
        """
        # using PIT0&1, which runs off the bus clock (half system clock)
        base = self.timestamp_res
        n = limit(int(period/base/(1<<32)),0,(1<<8)-1)
        reload = limit(round(period / base/ (n+1)) - 1, 1, (1<<32)-1)
        actual = (reload + 1)*(n+1) * base
        return actual, (n, reload)


@Board.supported(6)
class Teensy3_1(Board):
    names = ('Teensy 3.1',
             'Teensy 3.2',
            )
    CPU_clocks_per_tick = 2
    bandgap = 1
    # Note: all analog codes written assuming ADC0 and channel b
    CHANB=64
    ADC1=128
    analogs = ( 
        ('A0', 5|CHANB),      # PTD1  ADC0_SE5b
        ('A1', 14),     # PTC0  ADC0_SE14
        ('A2', 8),      # PTB0  ADC0_SE8, ADC1_SE8
        ('A3', 9),      # PTB1  ADC0_SE9, ADC1_SE9
        ('A4', 13),     # PTB3  ADC0_SE13
        ('A5', 12),     # PTB2  ADC0_SE12
        ('A6', 6|CHANB),      # PTD5  ADC0_SE6b
        ('A7', 7|CHANB),      # PTD6  ADC0_SE7b
        ('A8', 15),     # PTC1  ADC0_SE15
        ('A9', 4|CHANB),      # PTC2  ADC0_SE4b
        ('A10',0),      # ADC0_DP0 ADC1_DP3
        ('A11',19),     # ADC0_DM0 ADC1_DM3
        ('A12',3),      # ADC0_DP3 ADC1_DP1
#        ('A13',21),     # ADC0_DM3 ADC1_DM0    # Didn't work on ADC0 !
        ('A13',19|ADC1),     # ADC0_DM3 ADC1_DM0
        ('A14',23 ),    # DAC
        ('A15',5|ADC1), # D26   PTE1 ADC1_SE5a
        ('A16',5|CHANB|ADC1),   # D27   PTC9 ADC1_SE5b
        ('A17',4|CHANB|ADC1),   # D28   PTC8 ADC1_SE4b
        ('A18',6|CHANB|ADC1),   # D29   PTC10 ADC1_SE6b
        ('A19',7|CHANB|ADC1),   # D30   PTC11 ADC1_SE7b
        ('A20',4|ADC1), # D31   PTE0 ADC1_SE4a
        ('Temperature',26),  
        ('Bandgap 1V', 27),
        ('Vref 1.2V', 18|ADC1),         # didn't work on ADC0
#        ('Aref',29 )
       ) 

    PTA=0
    PTB=32
    PTC=64
    PTD=96
    PTE=128
    digitals = (
        ('D0',  PTB+16),        #PTB16
        ('D1',  PTB+17),        #PTB17
        ('D2',  PTD+0 ),        #PTD0
        ('D3',  PTA+12),        #PTA12
        ('D4',  PTA+13),        #PTA13
        ('D5',  PTD+7 ),        #PTD7
        ('D6',  PTD+4 ),        #PTD4
        ('D7',  PTD+2 ),        #PTD2
        ('D8',  PTD+3 ),        #PTD3
        ('D9',  PTC+3 ),        #PTC3
        ('D10', PTC+4 ),        #PTC4
        ('D11', PTC+6 ),        #PTC6
        ('D12', PTC+7 ),        #PTC7
        ('D13', PTC+5 ),        #PTC5
        # Digitals that overlap analogs not included
        #       (analog meaning takes precendence)
        # Consider trading off A15 and A20 to get extra frequency channel (Port E)
        ('D24', PTA+5),
        ('D25', PTB+19),
        ('D32', PTB+18),
        ('D33', PTA+4),         # NMI if port pin not made GPIO
    )
    DIFF=32
    differentials=(     # assuming ADC0 (swap for ADC1)
        ('A10-A11', DIFF+0),
        ('A12-A13', DIFF+3))
    eint = digitals
    
    def make_frequencies(digitals,dma_ports):
        return [ [("f({0})".format(d[0]),d[1]) for d in digitals if (d[1] & ~0x1f) == port] for port in dma_ports]
    frequencies=make_frequencies(digitals, (PTB,PTD,PTA,PTC,PTE))

    intsense = (
        ('rises', 1),
        ('falls',  2),
        ('changes', 3),
        )
    default_aref = 'AREF'
    aref = (
        ('AREF', 0),
        ('1.2V', 1))
    avg = (
        ('1', 0),
        ('4', 4),
        ('8', 5),
        ('16', 6),
        ('32', 7))
    default_avg='32'
    # Programmable Gain Amplifier settings not done yet
    # Use of ADC1 not done yet
    

    frequency_dead_cycles = 34       #  dead time in frequency counter (about 34 cycles)

    def timer_calc(self, period):
        """computes counter parameters
                n is index for prescaler
                reload is counter period-1 in prescaled ticks
                actual time in seconds
            returns (actual, (n,reload))
        """
        # using PIT0&1, which runs off the bus clock (half system clock)
        base = self.timestamp_res
        n = limit(int(period/base/(1<<32)),0,(1<<8)-1)
        reload = limit(round(period / base/ (n+1)) - 1, 1, (1<<32)-1)
        actual = (reload + 1)*(n+1) * base
        return actual, (n, reload)


@Board.supported(7)
class Teensy_LC(Board):
    names = ('Teensy LC',)
    CPU_clocks_per_tick = 2
    bandgap = 1
    CHANB=0x40
    DIFF=0x20
    analogs = ( 
        ('A0', CHANB+5),        # PTD1  ADC0_SE5b
        ('A1', 14),             # PTC0  ADC0_SE14
        ('A2',  8),     # PTB0  ADC0_SE8
        ('A3',  9),     # PTB1  ADC0_SE9
        ('A4',  13),    # PTB3  ADC0_SE13
        ('A5',  12),    # PTB2  ADC0_SE12
        ('A6',  CHANB+6),       # PTD5  ADC0_SE6b
        ('A7',  CHANB+7),       # PTD6  ADC0_SE7b
        ('A8',  15),    # PTC1  ADC0_SE15
        ('A9',  11),    # PTC2  ADC0_SE11
        ('A10', 0),     # PTE20  ADC0_SE0
        ('A11', 4),     # PTE21  ADC0_SE4a
        ('A12', 23),    # PTE30  ADC0_SE23
        ('Temperature',26),  
        ('Bandgap 1V', 27),
#        ('Aref',29 )
       ) 
    # D pins only defined through D13 (to avoid conflict with A pins)
    PTA=0
    PTB=32
    PTC=64
    PTD=96
    digitals = (
        ('D0',  PTB+16),
        ('D1',  PTB+17),
        ('D2',  PTD+0 ),
        ('D3',  PTA+1),
        ('D4',  PTA+2),
        ('D5',  PTD+7 ),
        ('D6',  PTD+4 ),
        ('D7',  PTD+2 ),
        ('D8',  PTD+3 ),
        ('D9',  PTC+3 ),
        ('D10', PTC+4 ),
        ('D11', PTC+6 ),
        ('D12', PTC+7 ),
        ('D13', PTC+5 ) 
        # digitals that overlap analogs not written out yet
    )
    DIFF=32
    differentials=(
        ('A10-A11', DIFF+0),
        )
    def make_eint(digitals,interrupt_ports):
        # This strange function is here because list comprehensions
        # ignore the class-scoped variables in Python3.
        return [d for d in digitals if ((d[1] & ~0x1f) in interrupt_ports)]
    eint=make_eint(digitals, (PTD,PTA,PTC))
    
    def make_frequencies(digitals,dma_ports):
        return [ [("f({0})".format(d[0]),d[1]) for d in digitals if (d[1] & ~0x1f) == port] for port in dma_ports]
    frequencies=make_frequencies(digitals, (PTA,PTC,PTD))
    
    intsense = (
        ('rises', 1),
        ('falls',  2),
        ('changes', 3),
        )
    default_aref = 'Power'
    aref = (
        ('Power', 1),
        ('AREF', 0))
    avg = (
        ('1', 0),
        ('4', 4),
        ('8', 5),
        ('16', 6),
        ('32', 7))
    default_avg='32'
    
    frequency_dead_cycles = 19  # 19 cycles of dead time from DMAMUX disable to DMAMUX enable

    def timer_calc(self, period):
        """computes counter parameters
                n is index for prescaler
                reload is counter period-1 in prescaled ticks
                actual time in seconds
            returns (actual, (n,reload))
        """
        # using PIT0&1, which runs off the bus clock (half system clock)
        base = self.timestamp_res
        n = limit(int(period/base/(1<<32)),0,(1<<8)-1)
        reload = limit(round(period / base/ (n+1)) - 1, 1, (1<<32)-1)
        actual = (reload + 1)*(n+1) * base
        return actual, (n, reload)





def getboardinfo(model):
    boardnum = unpack_from('<H', model)[0]
    board = Board.by_id[boardnum]()
#    print("DEBUG: boardnum=", boardnum, "names=", board.names, file=sys.stderr)
    board.setup(model[2:])
    return board
