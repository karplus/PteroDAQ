import sys

def tk_patch_if_needed(root):
    """Check the tk version number.
    If we know of problems with that version, patch things as much as feasible.
    """
    
    version=root.globalgetvar('tk_version')
    fields=version.split('.')
    major,minor=int(fields[0]),int(fields[1])
    
    if (major,minor) < (8,6):
        # the tk.tcl file doesn't have the right bindings.
        #       Copy them from the 8.6 tk.tcl file
        root.tk.eval(
"""
switch -exact -- [tk windowingsystem] {
    "x11" {
        event add <<Cut>>               <Control-Key-x> <Key-F20> <Control-Lock-Key-X>
        event add <<Copy>>              <Control-Key-c> <Key-F16> <Control-Lock-Key-C>
        event add <<Paste>>             <Control-Key-v> <Key-F18> <Control-Lock-Key-V>
        event add <<PasteSelection>>    <ButtonRelease-2>
        event add <<Undo>>              <Control-Key-z> <Control-Lock-Key-Z>
        event add <<Redo>>              <Control-Key-Z> <Control-Lock-Key-z>
        event add <<ContextMenu>>       <Button-3>
        # On Darwin/Aqua, buttons from left to right are 1,3,2.  On Darwin/X11 with recent
        # XQuartz as the X server, they are 1,2,3; other X servers may differ.

        event add <<SelectAll>>         <Control-Key-slash>
        event add <<SelectNone>>        <Control-Key-backslash>
        event add <<NextChar>>          <Right>
        event add <<SelectNextChar>>    <Shift-Right>
        event add <<PrevChar>>          <Left>
        event add <<SelectPrevChar>>    <Shift-Left>
        event add <<NextWord>>          <Control-Right>
        event add <<SelectNextWord>>    <Control-Shift-Right>
        event add <<PrevWord>>          <Control-Left>
        event add <<SelectPrevWord>>    <Control-Shift-Left>
        event add <<LineStart>>         <Home>
        event add <<SelectLineStart>>   <Shift-Home>
        event add <<LineEnd>>           <End>
        event add <<SelectLineEnd>>     <Shift-End>
        event add <<PrevLine>>          <Up>
        event add <<NextLine>>          <Down>
        event add <<SelectPrevLine>>    <Shift-Up>
        event add <<SelectNextLine>>    <Shift-Down>
        event add <<PrevPara>>          <Control-Up>
        event add <<NextPara>>          <Control-Down>
        event add <<SelectPrevPara>>    <Control-Shift-Up>
        event add <<SelectNextPara>>    <Control-Shift-Down>
        event add <<ToggleSelection>>   <Control-ButtonPress-1>

        # Some OS's define a goofy (as in, not <Shift-Tab>) keysym that is
        # returned when the user presses <Shift-Tab>. In order for tab
        # traversal to work, we have to add these keysyms to the PrevWindow
        # event. We use catch just in case the keysym isn't recognized.

        # This is needed for XFree86 systems
        catch { event add <<PrevWindow>> <ISO_Left_Tab> }
        # This seems to be correct on *some* HP systems.
        catch { event add <<PrevWindow>> <hpBackTab> }

        trace add variable ::tk_strictMotif write ::tk::EventMotifBindings
        set ::tk_strictMotif $::tk_strictMotif
        # On unix, we want to always display entry/text selection,
        # regardless of which window has focus
        set ::tk::AlwaysShowSelection 1
    }
    "win32" {
        event add <<Cut>>               <Control-Key-x> <Shift-Key-Delete> <Control-Lock-Key-X>
        event add <<Copy>>              <Control-Key-c> <Control-Key-Insert> <Control-Lock-Key-C>
        event add <<Paste>>             <Control-Key-v> <Shift-Key-Insert> <Control-Lock-Key-V>
        event add <<PasteSelection>>    <ButtonRelease-2>
        event add <<Undo>>              <Control-Key-z> <Control-Lock-Key-Z>
        event add <<Redo>>              <Control-Key-y> <Control-Lock-Key-Y>
        event add <<ContextMenu>>       <Button-3>

        event add <<SelectAll>>         <Control-Key-slash> <Control-Key-a> <Control-Lock-Key-A>
        event add <<SelectNone>>        <Control-Key-backslash>
        event add <<NextChar>>          <Right>
        event add <<SelectNextChar>>    <Shift-Right>
        event add <<PrevChar>>          <Left>
        event add <<SelectPrevChar>>    <Shift-Left>
        event add <<NextWord>>          <Control-Right>
        event add <<SelectNextWord>>    <Control-Shift-Right>
        event add <<PrevWord>>          <Control-Left>
        event add <<SelectPrevWord>>    <Control-Shift-Left>
        event add <<LineStart>>         <Home>
        event add <<SelectLineStart>>   <Shift-Home>
        event add <<LineEnd>>           <End>
        event add <<SelectLineEnd>>     <Shift-End>
        event add <<PrevLine>>          <Up>
        event add <<NextLine>>          <Down>
        event add <<SelectPrevLine>>    <Shift-Up>
        event add <<SelectNextLine>>    <Shift-Down>
        event add <<PrevPara>>          <Control-Up>
        event add <<NextPara>>          <Control-Down>
        event add <<SelectPrevPara>>    <Control-Shift-Up>
        event add <<SelectNextPara>>    <Control-Shift-Down>
        event add <<ToggleSelection>>   <Control-ButtonPress-1>
    }
    "aqua" {
        event add <<Cut>>               <Command-Key-x> <Key-F2> <Command-Lock-Key-X>
        event add <<Copy>>              <Command-Key-c> <Key-F3> <Command-Lock-Key-C>
        event add <<Paste>>             <Command-Key-v> <Key-F4> <Command-Lock-Key-V>
        event add <<PasteSelection>>    <ButtonRelease-3>
        event add <<Clear>>             <Clear>
        event add <<ContextMenu>>       <Button-2>

        # Official bindings
        # See http://support.apple.com/kb/HT1343
        event add <<SelectAll>>         <Command-Key-a>
        event add <<SelectNone>>        <Option-Command-Key-a>
        event add <<Undo>>              <Command-Key-z> <Command-Lock-Key-Z>
        event add <<Redo>>              <Shift-Command-Key-z> <Shift-Command-Lock-Key-z>
        event add <<NextChar>>          <Right> <Control-Key-f> <Control-Lock-Key-F>
        event add <<SelectNextChar>>    <Shift-Right> <Shift-Control-Key-F> <Shift-Control-Lock-Key-F>
        event add <<PrevChar>>          <Left> <Control-Key-b> <Control-Lock-Key-B>
        event add <<SelectPrevChar>>    <Shift-Left> <Shift-Control-Key-B> <Shift-Control-Lock-Key-B>
        event add <<NextWord>>          <Option-Right>
        event add <<SelectNextWord>>    <Shift-Option-Right>
        event add <<PrevWord>>          <Option-Left>
        event add <<SelectPrevWord>>    <Shift-Option-Left>
        event add <<LineStart>>         <Home> <Command-Left> <Control-Key-a> <Control-Lock-Key-A>
        event add <<SelectLineStart>>   <Shift-Home> <Shift-Command-Left> <Shift-Control-Key-A> <Shift-Control-Lock-Key-A>
        event add <<LineEnd>>           <End> <Command-Right> <Control-Key-e> <Control-Lock-Key-E>
        event add <<SelectLineEnd>>     <Shift-End> <Shift-Command-Right> <Shift-Control-Key-E> <Shift-Control-Lock-Key-E>
        event add <<PrevLine>>          <Up> <Control-Key-p> <Control-Lock-Key-P>
        event add <<SelectPrevLine>>    <Shift-Up> <Shift-Control-Key-P> <Shift-Control-Lock-Key-P>
        event add <<NextLine>>          <Down> <Control-Key-n> <Control-Lock-Key-N>
        event add <<SelectNextLine>>    <Shift-Down> <Shift-Control-Key-N> <Shift-Control-Lock-Key-N>
        # Not official, but logical extensions of above. Also derived from
        # bindings present in MS Word on OSX.
        event add <<PrevPara>>          <Option-Up>
        event add <<NextPara>>          <Option-Down>
        event add <<SelectPrevPara>>    <Shift-Option-Up>
        event add <<SelectNextPara>>    <Shift-Option-Down>
        event add <<ToggleSelection>>   <Command-ButtonPress-1>
    }
}
"""     )
