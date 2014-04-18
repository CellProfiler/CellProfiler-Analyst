
from .util.version import get_normalized_version
__version__ = get_normalized_version()
import properties
import dbconnect

properties = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()
