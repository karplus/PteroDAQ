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
    timestamp_res = 1e-6 # microsecond
    def timer_calc(self, period):
        # using Timer1
        prescales = (1, 8, 64, 256, 1024)
        base = self._tmr_base
        for n, pr in enumerate(prescales):
            if period <= ((1<<17) - 2) * pr * base:
                break
        top = limit(round(period / (2 * pr * base)), 3, (1<<16)-1)
        actual = (2 * pr * top * base)
        return actual, (n, top)
    def setup(self, model):
        if model[0] == 'a':
            self._tmr_base = 1.0/8e6
        elif model[0] == 'b':
            self._tmr_base = 1.0/16e6
        self.power_voltage = 1024./(unpack_from('<H', model, 1)[0]/1.1)

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
        ('D0', 32),
        ('D1', 33),
        ('D2', 34),
        ('D3', 35),
        ('D4', 36),
        ('D5', 37),
        ('D6', 38),
        ('D7', 39),
        ('D8', 0),
        ('D9', 1),
        ('D10', 2),
        ('D11', 3),
        ('D12', 4),
        ('D13', 5),
        ('A0', 16),
        ('A1', 17),
        ('A2', 18),
        ('A3', 19),
        ('A4', 20),
        ('A5', 21))
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
        ('D0', 34),
        ('D1', 35),
        ('D2', 33),
        ('D3', 32),
        ('D4', 36),
        ('D5', 22),
        ('D6', 39),
        ('D7', 54),
        ('D8', 4),
        ('D9', 5),
        ('D10', 6),
        ('D11', 7),
        ('D12', 38),
        ('D13', 23),
        ('A0', 71),
        ('A1', 70),
        ('A2', 69),
        ('A3', 68),
        ('A4', 65),
        ('A5', 64),
        ('SCK', 1),
        ('MOSI', 2),
        ('MISO', 3))
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
    analog_signed = (
        'Diff/PTE20-PTE21',
        'Diff/PTE22-PTE23')
    timestamp_res = 1/48e6 # approximately 0.02 microseconds
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
