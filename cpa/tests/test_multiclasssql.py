import mock
from unittest import TestCase
import cpa.multiclasssql

class WhereClausesTestCase(TestCase):
    def _where_clauses(self, imkeys):
        p = mock.Mock()
        p.table_id = None
        p.image_id = 'ImageNumber'
        p.object_table = 'Per_Object'
        dm = mock.Mock()
        filter_name = None
        dm.GetAllImageKeys = lambda x: imkeys
        return cpa.multiclasssql._where_clauses(p, dm, filter_name)

    def test_2(self):
        result = self._where_clauses([(2,), (1,)])
        print(result)
        assert result == ['(1 = 1)']

    def test_5(self):
        result = self._where_clauses([(5,), (4,), (3,), (2,), (1,)])
        assert result == ['(Per_Object.ImageNumber <= 5)']


