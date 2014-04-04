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

        
class AppendColumnTestCase(unittest.TestCase):
    def setUp(self):
        self.db = cpa.dbconnect.DBConnect.getInstance()
        self.p = cpa.dbconnect.p
        self.p.image_table = 'Per_Image'
        self.p.object_table = 'Per_Object'

    def test_not_user_image(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('Per_Image', 'foo', 'TEXT'))

    @patch.object(cpa.dbconnect.DBConnect, 'execute')
    def test_user_image(self, execute):
        self.db.AppendColumn('Per_Image', 'User_foo', 'TEXT')
        execute.assert_called_with('ALTER TABLE Per_Image ADD User_foo TEXT')

    def test_not_user_object(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('Per_Object', 'foo', 'TEXT'))

    @patch.object(cpa.dbconnect.DBConnect, 'execute')
    def test_user_object(self, execute):
        self.db.AppendColumn('Per_Object', 'usEr_foo', 'TEXT')
        execute.assert_called_with('ALTER TABLE Per_Object ADD usEr_foo TEXT')

    @patch.object(cpa.dbconnect.DBConnect, 'execute')
    def test_not_user_other(self, execute):
        self.db.AppendColumn('MetadataTable', 'foo', 'TEXT')
        execute.assert_called_with('ALTER TABLE MetadataTable ADD foo TEXT')

    def test_blank_name(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', '', 'TEXT'))

    def test_start_number(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', '1s', 'TEXT'))

    def test_symbol(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', 'foo$bar', 'TEXT'))
