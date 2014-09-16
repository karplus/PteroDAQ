from struct import unpack_from

def limit(x, a, b):
    if x < a:
        return a
    if x > b:
        return b
    return x

class Board(object):
    by_id = []
    @classmethod
    def supported(cls, brd):
        cls.by_id.append(brd)
        return brd

class ArduinoAVR(Board):
    intsense = (
        ('rises', 3),
        ('falls', 2),
        ('changes', 1),
        #('is low', 0)
        # removed due to lack of rate-limiting causing hang
        )
    avg = (
        ('1', 1),)
    analog_signed = ()
    timestamp_res = 0.5e-6 # half-microsecond
    def timer_calc(self, period):
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
        m = unpack_from('<HH', model, 0)
        self._tmr_base = 1./(m[0]*1000) # frequency given in kHz
        self.power_voltage = 65536./(m[1]/1.1) # 10 bit ADC, but left aligned to 16 bits

@Board.supported
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

@Board.supported
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

@Board.supported
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
        ('D13', 23)) # todo: finish
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

@Board.supported
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
        ('Bandgap', 30)) # todo: differential
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

@Board.supported
class FreedomKL25(Board):
    names = ('FRDM-KL25Z',)
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
        ('Diff/PTE20-PTE21', 32),
        ('Diff/PTE22-PTE23', 35),
        ('Temperature', 26),
        ('Bandgap', 27),
        ('Aref', 29)) # todo: internal differentials
    digitals = tuple(('PT{}{}'.format(port[0], pin), (n * 32 + pin)) for n, port in enumerate((
            ('A', (1, 2, 4, 5, 12, 13, 14, 15, 16, 17)),
            ('B', (0, 1, 2, 3, 8, 9, 10, 11)),
            ('C', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17)),
            ('D', (0, 1, 2, 3, 4, 5, 6, 7)),
            ('E', (0, 1, 2, 3, 4, 5, 20, 21, 22, 23, 30, 31))
        )) for pin in port[1])
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
    analog_signed = (
        'Diff/PTE20-PTE21',
        'Diff/PTE22-PTE23')
    timestamp_res = 1/24e6 # approximately 0.04 microseconds
    #power_voltage = 3.3
    def timer_calc(self, period):
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
        self.power_voltage = 65536./(unpack_from('<H', model)[0])

def getboardinfo(model):
    boardnum = unpack_from('<H', model)[0]
    board = Board.by_id[boardnum-1]()
    board.setup(model[2:])
    return board
