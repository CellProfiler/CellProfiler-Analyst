import wx

CHECK_FOR_UPDATES = 'CheckForUpdates'
CHECKFORNEWVERSIONS = 'CheckForNewVersions'
SKIPVERSION = 'SkipVersion'

def get_config():
    try:
        config = wx.Config.Get(False)
    except wx.PyNoAppError:
        app = wx.App(0)
        config = wx.Config.Get(False)
    if not config:
        wx.Config.Set(wx.Config('CellProfilerAnalyst','BroadInstitute','CellProfilerAnalystLocal.cfg','CellProfilerAnalystGlobal.cfg',wx.CONFIG_USE_LOCAL_FILE))
        config = wx.Config.Get()
    return config

def get_check_new_versions():
    if not get_config().Exists(CHECKFORNEWVERSIONS):
        # should this check for whether we can actually save preferences?
        return True
    return get_config().ReadBool(CHECKFORNEWVERSIONS)
    
def set_check_new_versions(val):
    old_val = get_check_new_versions()
    get_config().WriteBool(CHECKFORNEWVERSIONS, bool(val))
    # If the user turns on version checking, they probably don't want
    # to skip versions anymore.
    if val and (not old_val):
        set_skip_version(0)

def get_skip_version():
    if not get_config().Exists(SKIPVERSION):
        return 0
    return get_config().ReadInt(SKIPVERSION)

def set_skip_version(ver):
    get_config().WriteInt(SKIPVERSION, ver)

def get_check_update():
    if not get_config().Exists(CHECK_FOR_UPDATES):
        return "Never"
    return get_config().Read(CHECK_FOR_UPDATES)


def get_check_update_bool():
    if not get_config().Exists(CHECK_FOR_UPDATES):
        return True
    update_str = get_config().Read(CHECK_FOR_UPDATES)
    if update_str == "Disabled":
        return False
    else:
        return True


def set_check_update(val):
    if str(val) == "False":
        val = "Disabled"
    elif str(val) == "True":
        val = "Never"
    get_config().Write(CHECK_FOR_UPDATES, val)
