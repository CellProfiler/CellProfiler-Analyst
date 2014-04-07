
from .util.version import version_number as __version__
import properties
import dbconnect

properties = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()
