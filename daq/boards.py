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
    
    eint = ()   # tuple of pairs (interrupt pin name, interrupt number)
    aref = ()   # tuple of pairs (analog reference name, code from data sheet)
    
    intsense = ()       # tuple of pairs
                        # (triggering type name, numeric code)
                        # 'rises', 'falls', 'changes'
                        # Ordered for human interface.
    
    avg = ()            # tuple of pairs
                        # hardware averaging options for board
                        # (name of option, numeric code)
    
    default_avg = '1'   # default averaging is to use none (averaging 1 sample)
                        # but can be overridden in specific boards
    
    timestamp_res = None # resolution of timestamps in seconds
    power_voltage = None # power supply voltage, needed for analog reference info

    def __init__(self):
        """Build dict self.name_from_probe, mapping probes to names.
        Build dict self.probe_from_name, mapping names to probes.
        """
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
    
    def is_digital(self,name):
        """Is this the name for a digital channel?"""
        return name in (x[0] for x in self.digitals)
    
    @classmethod
    def supported(cls, model_num):
        """class decorator for appending subclasses to 
        Board's dictionary of supported boards
        """
        def decorator(brd):
            cls.by_id[model_num]=brd
            return brd
        return decorator
        
class ArduinoAVR(Board):
    """Board description abstract class for Arduino boards
    and compatibles using AVR processors
    """
    
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
    timestamp_res = 0.5e-6 # half-microsecond
    
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
    
    def setup(self, model):
        """unpacks model information sent from model info command
            and updates parameters for power_voltage and _tmr_base
        """
        m = unpack_from('<HH', model, offset=0)
#        print("DEBUG: m=", m, "self.bandgap=", self.bandgap, file=sys.stderr)
        self.power_voltage = 65536./(m[0]/self.bandgap) # 10 bit ADC, but left aligned to 16 bits
        self._tmr_base = 1./(m[1]*1000) # frequency given in kHz

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
    aref = (
        ('Power', 1),
        ('External', 0),
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
    aref = (
        ('Power', 1),
        ('External', 0),
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
    aref = (
        ('Power', 1),
        ('External', 0),
        ('2.56V', 3))

@Board.supported(5)
class FreedomKL25(Board):
    names = ('FRDM-KL25Z',)
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
        ('Aref', 29)) # To Do: internal differentials?
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
    eint = tuple(x for x in digitals if x[0][2] in ('A', 'D'))
    intsense = (
        ('rises', 1),
        ('falls', 2),
        ('changes', 3),
        #('is low', 0),
        #('is high', 4)
        # removed due to lack of rate-limiting causing hang
        )
    aref = (
        ('Power', 1),
        ('External', 0))
    avg = (
        ('1', 0),
        ('4', 4),
        ('8', 5),
        ('16', 6),
        ('32', 7))
    default_avg='4'
    
    timestamp_res = 1/24e6 # approximately 0.04 microseconds

    def timer_calc(self, period):
        """computes counter parameters
                n is index for prescaler
                reload is counter period-1 in prescaled ticks
                actual time in seconds
            returns (actual, (n,reload))
        """
        # using SysTick
        base = 1./48000000
        if period <= (1<<24)*base:
            pr = 1
            n = 1
        else:
            pr = 16
            n = 0
        reload = limit(round(period / (pr * base)) - 1, 1, (1<<24)-1)
        actual = (reload + 1) * pr * base
        return actual, (n, reload)
    
    def setup(self, model):
        """unpacks model information sent from model info command
            and updates parameters for power_voltage
        """
        self.power_voltage = 65536./(unpack_from('<H', model)[0]/self.bandgap)

def getboardinfo(model):
    boardnum = unpack_from('<H', model)[0]
    board = Board.by_id[boardnum]()
#    print("DEBUG: boardnum=", boardnum, "names=", board.names, file=sys.stderr)
    board.setup(model[2:])
    return board
