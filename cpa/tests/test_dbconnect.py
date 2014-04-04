import threading
from mock import patch, Mock
import unittest
import cpa.dbconnect


class ExecuteTestCase(unittest.TestCase):

    def setUp(self):
        self.p = cpa.dbconnect.p
        self.db = cpa.dbconnect.DBConnect.getInstance()
        cursor = Mock()
        connID = threading.currentThread().getName()
        self.db.connections[connID] = Mock()
        self.db.cursors[connID] = cursor

    def test_args_to_sqlite(self):
        self.p.db_type = 'SQLite'
        self.assertRaises(TypeError, lambda: self.db.execute('query', 'args'))

        
        
