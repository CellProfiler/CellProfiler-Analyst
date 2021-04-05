from mock import patch
import unittest
import cpa.datamodel

class PopulatePlateMapsTestCase(unittest.TestCase):

    def setUp(self):
        self.dm = cpa.datamodel.DataModel()
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

    @patch('cpa.datamodel.db')
    def test_A01_over_52_rows(self, db):
        # Need at least one well to trigger the code.
        db.execute.return_value = [('A01',),] 
        self.p.well_format = 'A01'
        self.p.plate_shape = (53, 1)
        self.assertRaises(ValueError, lambda: self.dm.populate_plate_maps())


class GetWellPositionFromName(unittest.TestCase):
    def setUp(self):
        self.dm = cpa.datamodel.DataModel()
        self.set_plate_map()

    def set_plate_map(self):
        self.dm.plate_map = {'A01': (0, 0)}
        self.dm.rev_plate_map = {(0, 0): 'A01'}

    def clear_plate_map(self):
        self.dm.plate_map = {}
        self.dm.rev_plate_map = {}

    @patch.object(cpa.datamodel.DataModel, 'populate_plate_maps')
    def test_forward_missing(self, populate_plate_maps):
        populate_plate_maps.side_effect = self.set_plate_map
        self.clear_plate_map()
        row, col = self.dm.get_well_position_from_name('A01')
        populate_plate_maps.assert_called_with()
        self.assertEqual((row, col), (0, 0))

    @patch.object(cpa.datamodel.DataModel, 'populate_plate_maps')
    def test_reverse_missing(self, populate_plate_maps):
        populate_plate_maps.side_effect = self.set_plate_map
        self.clear_plate_map()
        name = self.dm.get_well_name_from_position((0, 0))
        populate_plate_maps.assert_called_with()
        self.assertEqual(name, 'A01')

    def test_forward_present(self):
        self.assertEqual(self.dm.get_well_position_from_name('A01'),
                         (0, 0))

    def test_reverse_present(self):
        self.assertEqual(self.dm.get_well_name_from_position((0, 0)),
                         'A01')

    def test_forward_absent(self):
        self.assertRaises(KeyError, lambda: self.dm.get_well_position_from_name('B01'))

    def test_reverse_absent(self):
        self.assertRaises(KeyError, lambda: self.dm.get_well_name_from_position((1, 0)))
