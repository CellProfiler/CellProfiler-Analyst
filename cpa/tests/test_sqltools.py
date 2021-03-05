import unittest
from mock import patch, Mock
import threading
import os.path
import cpa


class TestOldFilter(unittest.TestCase):
    def setUp(self):
        fn = os.path.join(os.path.dirname(__file__),
                       'test_sqltools_old_filter.properties')
        p = cpa.properties.Properties()
        p.load_file(fn)
        self.db = cpa.dbconnect.DBConnect()
        cursor = Mock()
        connID = threading.currentThread().getName()
        self.db.connections[connID] = Mock()
        self.db.cursors[connID] = cursor


    def test_get_tables(self):
        p = cpa.properties.Properties()
        filter = p._filters['MCF7wt']
        with patch.object(cpa.db, 'execute') as execute:
            with patch.object(cpa.db, 'GetResultColumnNames') as GetResultColumnNames:
                execute.return_value = [(1, 'SIMPLE', 'Morphology_Per_Image', 'ALL', None, None, None, None, 107760, 'Using where')]
                GetResultColumnNames.return_value = ['id', 'select_type', 'table', 'type', 'possible_keys', 'key', 'key_len', 'ref', 'rows', 'Extra']
                tables = filter.get_tables()
        self.assertEqual(tables, set(['Morphology_Per_Image']))
