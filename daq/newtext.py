import sys
from functools import partial


def ec(e, *args):
    return root.tk.call(e.widget, *args)
def rc(*args):
    return root.tk.call(*args)

def create_newtext(r):
    global root
    root = r
    
#    root.tk.globalsetvar('PY_TMP_VAR', 1)
#    rc('::tk::EventMotifBindings', 'PY_TMP_VAR', '', '')
#    root.tk.globalunsetvar('PY_TMP_VAR')
    if rc('tk', 'windowingsystem') == 'x11':
        rc('event', 'add', '<<SelectAll>>', '<Control-a>')
    
    b = partial(root.bind_class, 'newtext')
    
    b('<1>', b1)
    b('<Button1-Motion>', b1m)
    b('<Double-1>', d1)
    b('<Triple-1>', t1)
    b('<Shift-1>', b1m)
    b('<Key>', key)
    b('<<PrevChar>>', partial(arrow, '-', 'char'))
    b('<<NextChar>>', partial(arrow, '+', 'char'))
    b('<<PrevLine>>', partial(arrow, '-', 'line'))
    b('<<NextLine>>', partial(arrow, '+', 'line'))
    b('<<SelectPrevChar>>', partial(sarrow, '-', 'char'))
    b('<<SelectNextChar>>', partial(sarrow, '+', 'char'))
    b('<<SelectPrevLine>>', partial(sarrow, '-', 'line'))
    b('<<SelectNextLine>>', partial(sarrow, '+', 'line'))
    b('<Delete>', partial(delete, 0))
    b('<BackSpace>', partial(delete, 1))
    b('<Control-Key>', lambda e: None)
    b('<<Cut>>', cut)
    b('<<Copy>>', copy)
    b('<<Paste>>', paste)
    b('<<Undo>>', undo)
    b('<<Redo>>', redo)
    b('<<SelectAll>>', selall)
    b('<MouseWheel>', scroll)
    b('<4>', scroll)
    b('<5>', scroll)

def conf(e):
    ec(e, 'mark', 'set', 'anchor', 'insert')
def b1(e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'mark', 'set', 'insert', '@{0},{1}'.format(e.x, e.y))
    ec(e, 'mark', 'set', 'anchor', 'insert')
    ec(e, 'see', 'insert')
    rc('focus', e.widget)
def b1m(e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'mark', 'set', 'insert', '@{0},{1}'.format(e.x, e.y))
    if ec(e, 'compare', 'anchor', '<', 'insert'):
        ec(e, 'tag', 'add', 'sel', 'anchor', 'insert')
    else:
        ec(e, 'tag', 'add', 'sel', 'insert', 'anchor')
    ec(e, 'see', 'insert')
def d1(e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'tag', 'add', 'sel', '@{0},{1} wordstart'.format(e.x, e.y), '@{0},{1} wordend'.format(e.x, e.y))
    ec(e, 'mark', 'set', 'anchor', 'sel.first')
    ec(e, 'mark', 'set', 'insert', 'sel.last')
    ec(e, 'see', 'insert')
def t1(e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'tag', 'add', 'sel', '@{0},{1} linestart'.format(e.x, e.y), '@{0},{1} lineend'.format(e.x, e.y))
    ec(e, 'mark', 'set', 'anchor', 'sel.first')
    ec(e, 'mark', 'set', 'insert', 'sel.last')
    ec(e, 'see', 'insert')
def key(e):
    if e.char == '\r':
        e.char = '\n'
    if not e.char:
        return
    if e.char=='\n':
        ec(e, 'edit', 'separator')
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'delete', 'insert', 'anchor', 'anchor', 'insert')
    ec(e, 'insert', 'insert', e.char)
    ec(e, 'see', 'insert')
def arrow(dir, size, e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'mark', 'set', 'insert', 'insert {0} 1 {1}s'.format(dir, size))
    ec(e, 'mark', 'set', 'anchor', 'insert')
    ec(e, 'see', 'insert')
def sarrow(dir, size, e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    ec(e, 'mark', 'set', 'insert', 'insert {0} 1 {1}s'.format(dir, size))
    if ec(e, 'compare', 'anchor', '<', 'insert'):
        ec(e, 'tag', 'add', 'sel', 'anchor', 'insert')
    else:
        ec(e, 'tag', 'add', 'sel', 'insert', 'anchor')
    ec(e, 'see', 'insert')
def delete(off, e):
    ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
    if ec(e, 'compare', 'anchor', '!=', 'insert'):
        ec(e, 'edit', 'separator')
        ec(e, 'delete', 'insert', 'anchor', 'anchor', 'insert')
    elif not off or ec(e, 'compare', 'insert', '!=', '0.0'):
        ec(e, 'delete', 'insert - {0} chars'.format(off))
    ec(e, 'see', 'insert')
def cut(e):
    if ec(e, 'tag', 'ranges', 'sel'):
        ec(e, 'edit', 'separator')
        t = ec(e, 'get', 'sel.first', 'sel.last')
        ec(e, 'delete', 'sel.first', 'sel.last')
        ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
        rc('clipboard', 'clear')
        rc('clipboard', 'append', t)
def copy(e):
    if ec(e, 'tag', 'ranges', 'sel'):
        t = ec(e, 'get', 'sel.first', 'sel.last')
        rc('clipboard', 'clear')
        rc('clipboard', 'append', t)
def paste(e):
    t = rc('clipboard', 'get')
    if t:
        ec(e, 'edit', 'separator')
        ec(e, 'tag', 'remove', 'sel', '0.0', 'end')
        ec(e, 'delete', 'insert', 'anchor', 'anchor', 'insert')
        ec(e, 'insert', 'insert', t)
        ec(e, 'see', 'insert')
def undo(e):
    try:
        ec(e, 'edit', 'undo')
    except tk.TclError:
        pass
def redo(e):
    try:
        ec(e, 'edit', 'redo')
    except tk.TclError:
        pass
def selall(e):
    ec(e, 'tag', 'add', 'sel', '0.0', 'end')
    ec(e, 'mark', 'set', 'insert', '0.0')
    ec(e, 'mark', 'set', 'anchor', 'end')
def scroll(e):
    if int(e.type) == 38: # 'MouseWheel'
        delta = -int(e.delta)
    elif e.num == 4:
        delta = -1
    else:
        delta = 1
    if delta >= 120 or delta <= -120:
        delta //= 120
    ec(e, 'yview', 'scroll', '{0}'.format(delta), 'units')
