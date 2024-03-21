
import logging
import wx
import sys
from .properties import Properties
from . import tableviewer
from . import dbconnect
import numpy as np

# TODO: Wrap queries in "SELECT * FROM (<query>) LIMIT 1000, offset"
#       and write a TableData subclass to feed rows to the TableViewer. 
class QueryMaker(wx.Frame):
    '''Super-simple interface for making queries directly to the database and
    displaying results using TableViewer. Results are pulled straight into 
    memory, so this shouldn't be used to fetch large result sets.
    '''
    def __init__(self, parent, size=(400,250), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Query Maker', **kwargs)
        panel = wx.Panel(self)
        self.query_textctrl = wx.TextCtrl(panel, -1, size=(-1,-1), style=wx.TE_MULTILINE)
        self.execute_btn = wx.Button(panel, -1, 'execute')

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        sizer.Add(self.query_textctrl, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 10)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(button_sizer, 0, wx.EXPAND)
        
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.execute_btn, 0, wx.ALL, 10)
        
        self.query_textctrl.Bind(wx.EVT_KEY_UP, self. on_enter)
        self.execute_btn.Bind(wx.EVT_BUTTON, self.on_execute)
        
    def on_enter(self, evt):
        '''Execute query on Cmd+Enter'''
        if evt.CmdDown() and evt.GetKeyCode() == wx.WXK_RETURN:
            self.on_execute()
        evt.Skip()
        
    def on_execute(self, evt=None):
        '''Run the query and show the results in a TableViewer'''
        db = dbconnect.DBConnect()
        q = self.query_textctrl.Value
        try:
            res = db.execute(q)
            if res is None or len(res) == 0:
                logging.info('Query successful. No Data to return.')
                return
            res = np.array(db.execute(q))
            colnames = db.GetResultColumnNames()
            grid = tableviewer.TableViewer(self, title='query results')
            grid.table_from_array(res, colnames)
            grid.Show()
            logging.info('Query successful')
        except Exception as e:
            logging.error('Query failed:')
            logging.error(e)


if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    p = Properties()
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print('Query Maker requires a properties file.  Exiting.')
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    QueryMaker(None).Show()

    app.MainLoop()

