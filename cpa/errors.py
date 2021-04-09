


def show_exception_as_dialog(type, value, tb, raisefurther=True):
    """Exception handler that show a dialog."""
    import traceback
    import wx

    # if tb:
    #     print((traceback.format_tb(tb)))

    if isinstance(value, ClearException):
        wx.MessageBox(value, value.heading, wx.OK | wx.ICON_ERROR)
    else:
        from wx.lib.dialogs import ScrolledMessageDialog
        lines = ['An error occurred in the program:\n']
        lines += traceback.format_exception_only(type, value)
        lines += ['\nTraceback (most recent call last):\n']
        if tb:
            lines += traceback.format_tb(tb)
        dlg = ScrolledMessageDialog(None, "".join(lines), 'Error', style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        dlg.ShowModal()
    if raisefurther:
        raise value


class ClearException(Exception):
    """
    AN exception where what happened is so clear that it is
    unnecessary to show a stack trace.
    
    """
    def __init__(self, message, heading='Error', *args, **kwargs):
        super(ClearException, self).__init__(message, *args, **kwargs)
        self.heading = heading


