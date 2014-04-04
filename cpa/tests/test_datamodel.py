from mock import patch
import unittest
import cpa.datamodel

class PopulatePlateMapsTestCase(unittest.TestCase):

    def setUp(self):
        self.dm = cpa.datamodel.DataModel.getInstance()
        self.p = cpa.datamodel.p

    @patch('cpa.datamodel.db')
    def test_well_format_A01(self, db):
        db.execute.return_value = [('A01',), ('P24',), ('b9',)]
        self.p.well_format = 'A01'
        self.p.plate_shape = (16, 24)
        self.dm.populate_plate_maps()

    @patch('cpa.datamodel.db')
    def test_well_format_123(self, db):
        db.execute.return_value = [('0',), ('01',), ('123',), ('12345',)]
        self.p.well_format = '123'
        self.p.plate_shape = (1, 20)
        self.dm.populate_plate_maps()

    def test_unknown_well_format(self):
        for value in [None, '', 'abc', 'AA1']:
            self.p.well_format = value
            self.assertRaises(ValueError, lambda: self.dm.populate_plate_maps())

        
