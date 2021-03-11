import datetime
import logging
import requests
import wx

from . import __version__ as current_version
from .cpaprefs import get_check_update, get_check_update_bool, set_check_update


def check_update(origin, force=False, event=True):
    if not force and not check_date():
        return
    if event:
        parent = origin.GetEventObject().GetWindow()
    else:
        parent = origin
    try:
        response = requests.get("https://api.github.com/repos/cellprofiler/cellprofiler-analyst/releases/latest", timeout=0.25)
    except:
        response = False
        message = "CellProfiler-Analyst was unable to connect to GitHub to check for updates"
    if response:
        status = response.status_code
        response = response.json()
        if status == 200 and 'tag_name' in response:
            latest = response['tag_name']
            latest = tuple(map(int, (latest.split("."))))
            current = tuple(map(int, (current_version.split("."))))
            if current < latest:
                body_text = response['body']
                if len(body_text) > 1000:
                    body_text = body_text[:1000] + "..."
                elif len(body_text) == 0:
                    body_text = "No information available"
                logging.info(f"An update for CellProfiler-Analyst is available ({response['tag_name']})")
                show_message(parent, response['tag_name'], body_text)
                return
            else:
                message = "CellProfiler-Analyst is up-to-date"
                if get_check_update() != "Disabled":
                    set_check_update(datetime.date.today().strftime("%Y%m%d"))
        elif status == 200:
            message = "Unable to read data from GitHub, API may have changed."
        else:
            message = "Invalid response from GitHub server, site may be down."
    if force:
        # User explicitly asked for a check, display a popup even with no available updates.
        dlg = wx.MessageDialog(
            parent,
            message,
            caption="Check for updates",
            style=wx.ICON_INFORMATION | wx.OK,
        )
        dlg.ShowModal()
    else:
        logging.info(message)


def show_message(parent, version, blurb):
    message = f"""A new CellProfiler-Analyst release is available:\n\nVersion {version}\n
Would you like to visit the download page?"""
    dlg = wx.RichMessageDialog(
        parent,
        message,
        caption="CellProfiler-Analyst Update Available",
        style=wx.YES_NO | wx.CENTRE | wx.ICON_INFORMATION,
    )
    dlg.ShowDetailedText(f"Release Notes:\n{blurb}")
    dlg.ShowCheckBox("Check for updates on startup", checked=get_check_update_bool())
    response = dlg.ShowModal()
    if response == wx.ID_YES:
        wx.LaunchDefaultBrowser("https://cellprofileranalyst.org/releases")
    if not dlg.IsCheckBoxChecked():
        set_check_update("Disabled")
    else:
        set_check_update(datetime.date.today().strftime("%Y%m%d"))


def check_date():
    last_checked = get_check_update()
    if last_checked == "Disabled":
        # Updating is disabled
        return False
    elif last_checked == "Never":
        return True
    today = datetime.date.today()
    last_checked = datetime.datetime.strptime(last_checked, "%Y%m%d").date()
    if (last_checked - today).days >= 7:
        return True
    else:
        return False