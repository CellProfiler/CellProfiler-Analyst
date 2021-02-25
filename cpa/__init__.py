
from .util.version import get_normalized_version
__version__ = get_normalized_version()
from . import properties
from . import dbconnect

properties = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()
