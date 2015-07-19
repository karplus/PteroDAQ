import Tkinter

def load_tile():
    root = Tkinter._default_root
    root.tk.call('package','require','tile')

class Widget(Tkinter.Widget):
    def __init__(self, master, widgetname, kw=None):
        root = Tkinter._default_root
        if not getattr(root, '_tile_loaded', False):
            root.tk.call('package','require','tile')
            root._tile_loaded = True
        Tkinter.Widget.__init__(self, master, widgetname, kw=kw)

class Button(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::button', kw)

class Checkbutton(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::checkbutton', kw)

class Entry(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::entry', kw)

class Combobox(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::combobox', kw)

class Frame(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::frame', kw)

class Label(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::label', kw)

class Radiobutton(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::radiobutton', kw)

class Scrollbar(Widget, Tkinter.Scrollbar):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::scrollbar', kw)

class Separator(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::separator', kw)

class Treeview(Widget):
    def __init__(self, master=None, **kw):
        Widget.__init__(self, master, 'ttk::treeview', kw)
    def get_children(self):
        return self.tk.call(self._w, 'children', '') or ()
    def delete(self, *items):
        self.tk.call(self._w, 'delete', items)
    def insert(self, parent, index, iid, text=''):
        return self.tk.call(self._w, 'insert', parent, index, '-id', iid, '-text', text)
    def item(self, item, option):
        return self.tk.call(self._w, 'item', item, '-'+option)
    def selection(self):
        return self.tk.call(self._w, 'selection')
    def selection_set(self, items):
        self.tk.call(self._w, 'selection', 'set', items)

