from cpa.util.version import __version__

from . import properties, util
from . import dbconnect

p = properties.Properties()
db = dbconnect.DBConnect()
