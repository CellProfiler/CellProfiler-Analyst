import wx
import cpa
import cpa.icons
from cpa.updatechecker import check_update
from cpa.util.version import display_version, __version__


def _on_check_update(self):
    check_update(self, force=True)

def _on_about(self):
    ''' Shows a message box with the version number etc.'''
    shift = wx.GetKeyState(wx.WXK_SHIFT)
    ctrl = wx.GetKeyState(wx.WXK_CONTROL)

    if shift or ctrl:
        import logging
        import os
        import sys
        import javabridge
        logging.info("\n\nDEBUG - CPA Java State is as follows:")

        # Hold ctrl only: change CP_JAVA_HOME
        if ctrl and not shift:
            cd = wx.DirDialog(None, message="Choose new CP_JAVA_HOME",
                       defaultPath=os.getcwd(), name="Set JAVA location")
            if cd.ShowModal() == wx.ID_OK:
                newdir = cd.GetPath()
                os.environ["CP_JAVA_HOME"] = newdir
                logging.info(f"Set CP_JAVA_HOME to {str(newdir)}")

        if 'CP_JAVA_HOME' in os.environ:
            logging.info(f"CP_JAVA_HOME is {os.environ['CP_JAVA_HOME']}")
        else:
            logging.info("CP_JAVA_HOME is not set")
        if 'JAVA_HOME' in os.environ:
            logging.info(f"JAVA_HOME is {os.environ['JAVA_HOME']}")
        else:
            logging.info("JAVA_HOME is not set")
        logging.info(f"Current working directory is {os.getcwd()}")
        logging.info(f"Python is running from {sys.prefix}")
        logging.info(f"Core Python install is at {sys.base_prefix}")
        logging.info(f"Javabridge java search returned {javabridge.locate.find_javahome()}")
        # Shift and ctrl/cmd held - test the VM. You'll need to restart CPA after since the VM can't be restarted.
        if shift and ctrl:
            try:
                logging.warning("Attempting to start Javabridge")
                javabridge.start_vm(run_headless=True)
                logging.warning("VM started successfully")
                javabridge.kill_vm()
                logging.warning("Shut down test vm. You'll need to RESTART CPA to use it again")
            except Exception as e:
                logging.info(f"Javabridge test failed")
                logging.info(e)

    message = ('CellProfiler Analyst was developed at The Broad Institute\n'
               'Imaging Platform and is distributed under the\n'
               'BSD 3-Clause License.')
    from wx.adv import AboutBox, AboutDialogInfo
    info = AboutDialogInfo()
    info.SetIcon(cpa.icons.get_cpa_icon())
    info.SetName('CellProfiler Analyst (%s)'%(str(display_version) or 'unknown revision'))
    info.SetDescription(message)
    info.AddDeveloper('David Dao')
    info.AddDeveloper('Adam Fraser')
    info.AddDeveloper('Jane Hung')
    info.AddDeveloper('Thouis (Ray) Jones')
    info.AddDeveloper('Vebjorn Ljosa')
    info.AddDeveloper('David Stirling')
    info.SetWebSite('cellprofileranalyst.org')
    AboutBox(info)

def make_help_menu(frame, main=False, manual_url="index.html"):
    help_version = __version__.rsplit('.', 1)[0]
    manual_url = f"https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-Analyst-{help_version}/{manual_url}"
    helpMenu = wx.Menu()
    def on_manual(self):
        import webbrowser
        webbrowser.open(manual_url)

    frame.Bind(wx.EVT_MENU, on_manual,
               helpMenu.Append(-1, item='Online manual'))
    if main:
        frame.Bind(wx.EVT_MENU, _on_check_update,
                   helpMenu.Append(-1, item='Check for updates', helpString='Check for new versions'))
    frame.Bind(wx.EVT_MENU, _on_about,
               helpMenu.Append(-1, item='About', helpString='About CellProfiler Analyst'))
    return helpMenu

if __name__ == '__main__':
    app = wx.App()
    frame = wx.Frame(None, title='Test help menu')
    menu_bar = wx.MenuBar()
    menu_bar.Append(make_help_menu(frame), 'Help')
    frame.SetMenuBar(menu_bar)
    frame.Show()
    app.MainLoop()

