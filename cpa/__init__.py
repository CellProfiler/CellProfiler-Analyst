
import cpa.util.version
__version__ = cpa.util.version.get_normalized_version()
import properties
import dbconnect

properties = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()
