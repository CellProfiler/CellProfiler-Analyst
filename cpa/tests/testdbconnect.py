import unittest
from dbconnect import *
from datamodel import DataModel
from properties import Properties
import numpy as np

class TestDBConnect(unittest.TestCase):
    def setup_mysql(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance( )
        self.db.Disconnect()
        self.p.LoadFile('../../CPAnalyst_test_data/nirht_test.properties')

    def setup_sqlite(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance()
        self.db.Disconnect()
        self.p.LoadFile('../../CPAnalyst_test_data/nirht_local.properties')
        
    def setup_sqlite2(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance()
        self.db.Disconnect()
        self.p.LoadFile('../../CPAnalyst_test_data/export_to_db_test.properties')
        
        
    #
    # Test module-level functions
    #
       
    def test_clean_up_colnames(self):
        self.setup_mysql()
    
    def test_well_key_columns(self):
        self.setup_mysql()
        assert well_key_columns() == ('plate', 'well')
        self.setup_sqlite()
        assert well_key_columns() == tuple()
        
    def test_image_key_columns(self):
        self.setup_mysql()
        assert image_key_columns() == ('ImageNumber',)
        self.setup_sqlite()
        assert image_key_columns() == ('TableNumber','ImageNumber')
    
    def test_object_key_columns(self):
        self.setup_mysql()
        assert object_key_columns() == ('ImageNumber','ObjectNumber')
        self.setup_sqlite()
        assert object_key_columns() == ('TableNumber', 'ImageNumber','ObjectNumber')
    
    def test_GetWhereClauseForObjects(self):
        self.setup_mysql()
        assert GetWhereClauseForObjects([(1,1)]) == '(ImageNumber=1 AND ObjectNumber=1)'
        assert GetWhereClauseForObjects([(1,1), (2,1)]) == '(ImageNumber=1 AND ObjectNumber=1 OR ImageNumber=2 AND ObjectNumber=1)'
        self.setup_sqlite()
        assert GetWhereClauseForObjects([(0,1,1), (0,2,1)]) == '(TableNumber=0 AND ImageNumber=1 AND ObjectNumber=1 OR TableNumber=0 AND ImageNumber=2 AND ObjectNumber=1)'
        
    def test_GetWhereClauseForImages(self):
        self.setup_mysql()
        assert GetWhereClauseForImages([(1,)]) == 'ImageNumber IN (1)'
        assert GetWhereClauseForImages([(1,), (2,)]) == 'ImageNumber IN (1,2)'
        self.setup_sqlite()
        assert GetWhereClauseForImages([(0,1), (0,2)]) == '(TableNumber=0 AND ImageNumber IN (1,2))'
    
    def test_UniqueObjectClause(self):
        self.setup_mysql()
        assert UniqueObjectClause() == 'ImageNumber,ObjectNumber'
        self.setup_sqlite()
        assert UniqueObjectClause() == 'TableNumber,ImageNumber,ObjectNumber'
    
    def test_UniqueImageClause(self):
        self.setup_mysql()
        assert UniqueImageClause() == 'ImageNumber'
        self.setup_sqlite()
        assert UniqueImageClause() == 'TableNumber,ImageNumber'
            

    #
    # Test class functions
    #

    def test_Connect_Disconnect(self):
        self.setup_mysql()
        self.db.connect()
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
        self.db.connect()
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
        self.db.Disconnect()
        assert len(self.db.connections)==0
        assert len(self.db.cursors)==0
        assert len(self.db.connectionInfo)==0
        
        self.setup_sqlite()
        assert len(self.db.connections)==0
        assert len(self.db.cursors)==0
        assert len(self.db.connectionInfo)==0
        self.db.GetAllImageKeys()
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
        self.db.GetAllImageKeys()
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
        self.db.Disconnect()
        assert len(self.db.connections)==0
        assert len(self.db.cursors)==0
        assert len(self.db.connectionInfo)==0

        
    def test_Commit(self):
        self.setup_mysql()
        self.db.connect()
        self.db.execute('DROP TABLE IF EXISTS temp_test')
        self.db.execute('CREATE TABLE temp_test (id int(11) default NULL)')
        self.db.execute('INSERT INTO temp_test values(1)')
        self.db.Commit()
        self.db.Disconnect()
        self.db.connect()
        res = self.db.execute('SELECT id FROM temp_test WHERE id=1')
        assert res == [(1L,)]
        self.db.execute('DROP TABLE temp_test')
    
    def test_execute(self):
        self.setup_mysql()
        self.db.execute('SELECT %s FROM %s'%(self.p.image_id,self.p.image_table))

        self.setup_sqlite()
        self.db.execute('SELECT %s FROM %s'%(self.p.image_id,self.p.image_table))

    def test_GetObjectIDAtIndex(self):
        self.setup_mysql()
        obKey = self.db.GetObjectIDAtIndex(imKey=(1,), index=94)
        assert obKey==(1,94)
        
        self.setup_sqlite()
        obKey = self.db.GetObjectIDAtIndex(imKey=(0,1), index=94)
        assert obKey==(0,1,94)

    def test_GetPerImageObjectCounts(self):
        self.setup_mysql()
        self.db.GetPerImageObjectCounts()
        
        self.setup_sqlite()
        self.db.GetPerImageObjectCounts()
        
    def test_GetObjectCoords(self):
        self.setup_mysql()
        xy = self.db.GetObjectCoords((1,1))
        assert xy==(11.4818, 305.06400000000002)
        
        self.setup_sqlite()
        xy = self.db.GetObjectCoords((0,1,1))
        assert xy==(11.4818, 305.06400000000002)
        
    def test_GetObjectNear(self):
        self.setup_mysql()
        obKey = self.db.GetObjectNear((1,), 11, 300)
        assert obKey == (1,1)
        
        self.setup_sqlite()
        obKey = self.db.GetObjectNear((0,1), 11, 300)
        assert obKey == (0,1,1)
        
    def test_GetFullChannelPathsForImage(self):
        self.setup_mysql()
        paths = self.db.GetFullChannelPathsForImage((1,))
        assert paths==['2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d2.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d1.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d0.DIB']
        
        self.setup_sqlite()
        paths = self.db.GetFullChannelPathsForImage((0,1))
        assert paths==['2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d2.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d1.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d0.DIB']
        
    def test_GetGroupMaps(self):
        self.setup_mysql()
        groupMaps, colNames = self.db.GetGroupMaps()
        assert groupMaps['Gene'][(1,)] == ('Gabra3',)
        assert groupMaps['Well'][(1,)] == (1L,)
        assert groupMaps['Well+Gene'][(1,)] == (1L, 'Gabra3')
        assert colNames == {'Gene': ['gene'], 'Well': ['well'], 'Well+Gene': ['well', 'gene']}
        
        self.setup_sqlite()
        groupMaps, colNames = self.db.GetGroupMaps()
        assert groupMaps['96x4'][(0,1)] == (0,1)
        assert colNames == {'96x4': ['T2', 'I2']}
        
    def test_GetFilteredImages(self):
        self.setup_mysql()
        test = set(self.db.GetFilteredImages('MAPs'))
        print test
        vals = set([(239L,), (21L,), (32L,), (197L,), (86L,), (23L,), (61L,), (72L,), (213L,), (222L,), (63L,), (229L,), (221L,), (38L,), (224L,), (231L,), (13L,), (24L,), (78L,), (214L,), (15L,), (223L,), (53L,), (64L,), (246L,), (55L,), (93L,), (232L,), (30L,), (206L,), (95L,), (215L,), (5L,), (16L,), (70L,), (7L,), (45L,), (56L,), (238L,), (198L,), (47L,), (207L,), (85L,), (96L,), (22L,), (87L,), (253L,), (8L,), (62L,), (254L,), (255L,), (199L,), (37L,), (48L,), (205L,), (230L,), (208L,), (39L,), (77L,), (88L,), (14L,), (79L,), (245L,), (256L,), (54L,), (247L,), (29L,), (40L,), (94L,), (31L,), (240L,), (69L,), (80L,), (6L,), (216L,), (71L,), (237L,), (248L,), (200L,), (46L,)])
        assert test == vals
        assert self.db.GetFilteredImages('IMPOSSIBLE') == []
        
        self.setup_sqlite()
        assert self.db.GetFilteredImages('FirstTen') == [(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),(0,10)]
        assert self.db.GetFilteredImages('IMPOSSIBLE') == []
        
    def test_GetColumnNames(self):
        self.setup_mysql()
        cols = self.db.GetColumnNames(self.p.object_table)
        assert cols[:19] == ['ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY', 'Nuclei_Children_Cells_Count', 'Nuclei_Correlation_Correlation_DNA_and_pH3', 'Nuclei_Correlation_Correlation_DNA_and_Actin', 'Nuclei_Correlation_Correlation_pH3_and_Actin', 'Nuclei_AreaShape_Area', 'Nuclei_AreaShape_Eccentricity', 'Nuclei_AreaShape_Solidity', 'Nuclei_AreaShape_Extent', 'Nuclei_AreaShape_Euler_number', 'Nuclei_AreaShape_Perimeter', 'Nuclei_AreaShape_Form_factor', 'Nuclei_AreaShape_MajorAxisLength', 'Nuclei_AreaShape_MinorAxisLength', 'Nuclei_AreaShape_Orientation', 'Nuclei_AreaShape_Zernike0_0']
        assert cols[-20:] == ['AreaNormalized_Cytoplasm_AreaShape_Zernike5_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike5_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_8', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_9']
        
        self.setup_sqlite()
        cols = self.db.GetColumnNames(self.p.object_table)
        assert cols[:20] == ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY', 'Nuclei_Children_Cells_Count', 'Nuclei_Correlation_Correlation_DNA_and_pH3', 'Nuclei_Correlation_Correlation_DNA_and_Actin', 'Nuclei_Correlation_Correlation_pH3_and_Actin', 'Nuclei_AreaShape_Area', 'Nuclei_AreaShape_Eccentricity', 'Nuclei_AreaShape_Solidity', 'Nuclei_AreaShape_Extent', 'Nuclei_AreaShape_Euler_number', 'Nuclei_AreaShape_Perimeter', 'Nuclei_AreaShape_Form_factor', 'Nuclei_AreaShape_MajorAxisLength', 'Nuclei_AreaShape_MinorAxisLength', 'Nuclei_AreaShape_Orientation', 'Nuclei_AreaShape_Zernike0_0']
        assert cols[-20:] == ['AreaNormalized_Cytoplasm_AreaShape_Zernike5_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike5_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_8', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_9']
        
    def test_GetColumnTypes(self):
        self.setup_mysql()
        cols = self.db.GetColumnTypes(self.p.object_table)
        assert cols[:19] == [long, long, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
        assert cols[-20:] == [float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
        cols = self.db.GetColumnTypes(self.p.image_table)
        assert cols[:20] == [long, long, long, str, long, str, str, str, str, str, str, float, float, float, float, float, float, float, float, float]
        
        
    def test_GetColnamesForClassifier(self):
        self.setup_mysql()
        cols = self.db.GetColnamesForClassifier()
        for c in ['ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY']:
            assert c not in cols
        
        self.setup_sqlite()
        cols = self.db.GetColnamesForClassifier()
        for c in ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY']:
            assert c not in cols
                     
    def test_ReadExportToDB(self):
        '''Test reading data from Export to Database.'''
        self.setup_sqlite2()
        vals = [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,), (11,), (12,), (13,), (14,), (15,), (16,), (17,), (18,), (19,), (20,)]
        groups = {'Plate+Well': {(u'Week1_22123', u'B05'): [(13,), (14,), (15,), (16,)], (u'Week1_22123', u'B02'): [(1,), (2,), (3,), (4,)], (u'Week1_22123', u'B04'): [(9,), (10,), (11,), (12,)], (u'Week1_22123', u'B06'): [(17,), (18,), (19,), (20,)], (u'Week1_22123', u'B03'): [(5,), (6,), (7,), (8,)]}}, {'Plate+Well': ['Image_Metadata_Plate_DAPI', 'Image_Metadata_Well_DAPI']}
        assert len(self.db.GetAllImageKeys())==20
        assert self.db.GetAllImageKeys() == vals
        assert self.db.GetGroupMaps(True) == groups
        
    def test_CreateMySQLTempTableFromData(self):
        self.setup_mysql()
        data = [['A01', 1, 1.],
                ['A02', 1, 2.],
                ['A03', 1, -np.inf],
                ['A04', 1, np.inf],
                ['A04', 1, np.nan],
                ['A04', 1, 100],
                ['A04', 1, 200],
                ]
        colnames = ['well', 'plate', 'vals']
        self.db.CreateTableFromData(data, colnames, '__test_table', temporary=True)
        res =  self.db.execute('select * from __test_table')
        assert res==[('A01', 1, 1.0), ('A02', 1, 2.0), ('A03', 1, None), ('A04', 1, None), ('A04', 1, None), ('A04', 1, 100.0), ('A04', 1, 200.0)]
        
    def test_CreateSQLiteTempTableFromData(self):
        self.setup_sqlite()
        data = [['A01', 1, 1.],
                ['A02', 1, 2.],
                ['A03', 1, -np.inf],
                ['A04', 1, np.inf],
                ['A04', 1, np.nan],
                ['A04', 1, 100],
                ['A04', 1, 200],
                ]
        colnames = ['well', 'plate', 'vals']
        self.db.CreateTableFromData(data, colnames, '__test_table', temporary=True)
        res =  self.db.execute('select * from __test_table')
        assert res==[('A01', 1, 1.0), ('A02', 1, 2.0), ('A03', 1, None), ('A04', 1, None), ('A04', 1, None), ('A04', 1, 100.0), ('A04', 1, 200.0)]
    
        
if __name__ == '__main__':
    unittest.main()        
