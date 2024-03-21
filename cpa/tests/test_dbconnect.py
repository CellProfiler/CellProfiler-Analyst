import threading
from mock import patch, Mock
import unittest
import cpa.dbconnect


class ExecuteTestCase(unittest.TestCase):

    def setUp(self):
        self.p = cpa.dbconnect.p
        self.db = cpa.dbconnect.DBConnect()
        cursor = Mock()
        connID = threading.currentThread().getName()
        self.db.connections[connID] = Mock()
        self.db.cursors[connID] = cursor

    def test_args_to_sqlite(self):
        self.p.db_type = 'SQLite'
        self.assertRaises(TypeError, lambda: self.db.execute('query', 'args'))

        
class CheckColnameUserTestCase(unittest.TestCase):
    def setUp(self):
        self.db = cpa.dbconnect.DBConnect()
        self.p = cpa.dbconnect.p
        self.p.image_table = 'Per_Image'
        self.p.object_table = 'Per_Object'
        self.f = cpa.dbconnect._check_colname_user

    def test_not_user_image(self):
        self.assertRaises(ValueError, lambda: self.f(self.p, 'Per_Image', 'foo'))

    def test_user_image(self):
        self.f(self.p, 'Per_Image', 'User_foo')

    def test_not_user_object(self):
        self.assertRaises(ValueError, lambda: self.f(self.p, 'Per_Object', 'foo'))

    def test_user_object(self):
        self.f(self.p, 'Per_Object', 'usEr_foo')

    def test_not_user_other(self):
        self.f(self.p, 'MetadataTable', 'foo')


class AppendColumnTestCase(unittest.TestCase):
    def setUp(self):
        self.db = cpa.dbconnect.DBConnect()
        self.p = cpa.dbconnect.p
        self.p.image_table = 'Per_Image'
        self.p.object_table = 'Per_Object'

    def test_blank_name(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', '', 'TEXT'))

    def test_start_number(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', '1s', 'TEXT'))

    def test_symbol(self):
        self.assertRaises(ValueError, lambda: self.db.AppendColumn('FooTable', 'foo$bar', 'TEXT'))


class UpdateWellsTestCase(unittest.TestCase):
    def setUp(self):
        self.db = cpa.dbconnect.DBConnect()
        self.p = cpa.dbconnect.p
        self.p.image_table = 'Per_Image'
        self.p.object_table = 'Per_Object'
        self.p.well_id = 'Well'

    def test_double_quote(self):
        with patch.object(self.db, 'execute') as execute:
            self.assertRaises(ValueError, lambda: self.db.UpdateWells("Per_Image", "User_BarColumn", 'baz"quux', [('A01',)]))

    def test_single_quote(self):
        with patch.object(self.db, 'execute') as execute:
            self.assertRaises(ValueError, lambda: self.db.UpdateWells("Per_Image", "User_BarColumn", "baz'quux", [('A01',)]))

    def test_backtick(self):
        with patch.object(self.db, 'execute') as execute:
            self.assertRaises(ValueError, lambda: self.db.UpdateWells("Per_Image", "User_BarColumn", "baz`quux", [('A01',)]))

    def test_null(self):
        with patch.object(self.db, 'execute') as execute:
            self.db.UpdateWells("Per_Image", "User_BarColumn", None, [('A01',)])
            execute.assert_called_with('UPDATE Per_Image SET User_BarColumn=NULL WHERE Well IN ("A01")')

    def test_string(self):
        with patch.object(self.db, 'execute') as execute:
            self.db.UpdateWells("Per_Image", "User_BarColumn", "baz", [('A01',)])
            execute.assert_called_with('UPDATE Per_Image SET User_BarColumn="baz" WHERE Well IN ("A01")')



