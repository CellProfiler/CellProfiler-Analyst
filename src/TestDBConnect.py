import unittest
from DBConnect import DBConnect
from DataModel import DataModel
from Properties import Properties
import numpy as np

class TestDBConnect(unittest.TestCase):
    def setup(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance( )
        self.db.Disconnect()
        self.p.LoadFile('../test_data/nirht_test.properties')

    def setup_local(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance()
        self.db.Disconnect()
        self.p.LoadFile('../test_data/nirht_local.properties')
        
    def setup_local2(self):
        self.p  = Properties.getInstance()
        self.db = DBConnect.getInstance()
        self.db.Disconnect()
        self.p.LoadFile('../test_data/export_to_db_test.properties')

    def test_Connect(self):
        self.setup()
        self.db.Connect(db_host=self.p.db_host, db_user=self.p.db_user,
                        db_passwd=self.p.db_passwd, db_name=self.p.db_name)
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
        self.db.Connect(db_host=self.p.db_host, db_user=self.p.db_user,
                        db_passwd=self.p.db_passwd, db_name=self.p.db_name)
        assert len(self.db.connections)==1
        assert len(self.db.cursors)==1
        assert len(self.db.connectionInfo)==1
    
    def test_execute(self):
        self.setup()
        self.db.execute('SELECT %s FROM %s'%(self.p.image_id,self.p.image_table))
        
    def test_GetObjectIDAtIndex(self):
        self.setup()
        obKey = self.db.GetObjectIDAtIndex(imKey=(0,1), index=94)
        assert obKey==(0,1,94)

    def test_GetPerImageObjectCounts(self):
        self.setup()
        self.db.GetPerImageObjectCounts()
        
    def test_GetObjectCoords(self):
        self.setup()
        xy = self.db.GetObjectCoords((0,1,1))
        assert xy==(11.4818, 305.06400000000002)
        
    def test_GetObjectNear(self):
        self.setup()
        obKey = self.db.GetObjectNear((0,1), 11, 300)
        assert obKey == (0,1,1)
        
    def test_GetFullChannelPathsForImage(self):
        self.setup()
        paths = self.db.GetFullChannelPathsForImage((0,1))
        assert paths==['2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d2.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d1.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d0.DIB']
        
    def test_GetGroupMaps(self):
        self.setup()
        groupMaps, colNames = self.db.GetGroupMaps()
        assert groupMaps['Gene'][(0,1)] == ('Gabra3',)
        assert groupMaps['Well'][(0,1)] == (1L,)
        assert groupMaps['Well+Gene'][(0,1)] == (1L, 'Gabra3')
        assert colNames == {'Gene': ['gene'], 'Well': ['well'], 'Well+Gene': ['well', 'gene']}
        
    def test_GetFilteredImages(self):
        self.setup()
        test = set(self.db.GetFilteredImages('MAPs'))
        vals = set([(0,77),(0,78),(0,79),(0,80),(0,69),(0,70),(0,71),(0,72),(0,61),(0,62),(0,63),(0,64),(0,53),(0,54),(0,55),(0,56),(0,45),(0,46),(0,47),(0,48),(0,37),(0,38),(0,39),(0,40),(0,29),(0,30),(0,31),(0,32),(0,21),(0,22),(0,23),(0,24),(0,13),(0,14),(0,15),(0,16),(0,5),(0,6),(0,7),(0,8),(0,253),(0,254),(0,255),(0,256),(0,245),(0,246),(0,247),(0,248),(0,237),(0,238),(0,239),(0,240),(0,229),(0,230),(0,231),(0,232),(0,221),(0,222),(0,223),(0,224),(0,213),(0,214),(0,215),(0,216),(0,205),(0,206),(0,207),(0,208),(0,197),(0,198),(0,199),(0,200),(0,93),(0,94),(0,95),(0,96),(0,85),(0,86),(0,87),(0,88L)])
        assert test == vals
        assert self.db.GetFilteredImages('IMPOSSIBLE') == []
        
    def test_GetColumnNames(self):
        self.setup()
        cols = self.db.GetColumnNames(self.p.object_table)
        assert cols[:20] == ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY', 'Nuclei_Children_Cells_Count', 'Nuclei_Correlation_Correlation_DNA_and_pH3', 'Nuclei_Correlation_Correlation_DNA_and_Actin', 'Nuclei_Correlation_Correlation_pH3_and_Actin', 'Nuclei_AreaShape_Area', 'Nuclei_AreaShape_Eccentricity', 'Nuclei_AreaShape_Solidity', 'Nuclei_AreaShape_Extent', 'Nuclei_AreaShape_Euler_number', 'Nuclei_AreaShape_Perimeter', 'Nuclei_AreaShape_Form_factor', 'Nuclei_AreaShape_MajorAxisLength', 'Nuclei_AreaShape_MinorAxisLength', 'Nuclei_AreaShape_Orientation', 'Nuclei_AreaShape_Zernike0_0']
        assert cols[-20:] == ['AreaNormalized_Cytoplasm_AreaShape_Zernike5_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike5_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_8', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_9']
        
    def test_GetColumnTypes(self):
        self.setup()
        cols = self.db.GetColumnTypes(self.p.object_table)
        assert cols[:20] == [long, long, long, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
        assert cols[-20:] == [float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]
        cols = self.db.GetColumnTypes(self.p.image_table)
        assert cols[:20] == [long, long, str, str, str, str, str, str, str, str, str, str, str, str, float, float, float, float, float, float]
        
        
    def test_GetColnamesForClassifier(self):
        self.setup()
        cols = self.db.GetColnamesForClassifier()
        for c in ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY']:
            assert c not in cols
            
    def test_GetCellDataForClassifier(self):
        self.setup()
        cellData = self.db.GetCellDataForClassifier((0,1,1))
        assert len(cellData) == 615
        
    #
    # Tests using csv files instead of DB
    #
        
    def test_Connect_local(self):
        # this one takes a while
        self.setup_local()
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

    def test_execute_local(self):
        self.setup_local()
        self.db.execute('SELECT %s FROM %s'%(self.p.image_id,self.p.image_table))
        
    def test_GetObjectIDAtIndex_local(self):
        self.setup_local()
        obKey = self.db.GetObjectIDAtIndex(imKey=(0,1), index=94)
        assert obKey==(0,1,94)

    def test_GetPerImageObjectCounts_local(self):
        self.setup_local()
        self.db.GetPerImageObjectCounts()
        
    def test_GetObjectCoords_local(self):
        self.setup_local()
        xy = self.db.GetObjectCoords((0,1,1))
        assert xy==(11.4818, 305.06400000000002)
        
    def test_GetObjectNear_local(self):
        self.setup_local()
        obKey = self.db.GetObjectNear((0,1), 11, 300)
        assert obKey == (0,1,1)
        
    def test_GetFullChannelPathsForImage_local(self):
        self.setup_local()
        paths = self.db.GetFullChannelPathsForImage((0,1))
        assert paths==['2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d2.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d1.DIB', 
                       '2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A01f00d0.DIB']
        
    def test_GetGroupMaps_local(self):
        self.setup_local()
        groupMaps, colNames = self.db.GetGroupMaps()
        assert groupMaps['96x4'][(0,1)] == (0,1)
        assert colNames == {'96x4': ['T2', 'I2']}
        
    def test_GetFilteredImages_local(self):
        self.setup_local()
        assert self.db.GetFilteredImages('FirstTen') == [(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),(0,10)]
        assert self.db.GetFilteredImages('IMPOSSIBLE') == []
        
    def test_GetColumnNames_local(self):
        self.setup_local()
        cols = self.db.GetColumnNames(self.p.object_table)
        assert cols[:20] == ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY', 'Nuclei_Children_Cells_Count', 'Nuclei_Correlation_Correlation_DNA_and_pH3', 'Nuclei_Correlation_Correlation_DNA_and_Actin', 'Nuclei_Correlation_Correlation_pH3_and_Actin', 'Nuclei_AreaShape_Area', 'Nuclei_AreaShape_Eccentricity', 'Nuclei_AreaShape_Solidity', 'Nuclei_AreaShape_Extent', 'Nuclei_AreaShape_Euler_number', 'Nuclei_AreaShape_Perimeter', 'Nuclei_AreaShape_Form_factor', 'Nuclei_AreaShape_MajorAxisLength', 'Nuclei_AreaShape_MinorAxisLength', 'Nuclei_AreaShape_Orientation', 'Nuclei_AreaShape_Zernike0_0']
        assert cols[-20:] == ['AreaNormalized_Cytoplasm_AreaShape_Zernike5_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike5_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike6_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike7_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_0', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_2', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_4', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_6', 'AreaNormalized_Cytoplasm_AreaShape_Zernike8_8', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_1', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_3', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_5', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_7', 'AreaNormalized_Cytoplasm_AreaShape_Zernike9_9']
        
    def test_GetColnamesForClassifier_local(self):
        self.setup_local()
        cols = self.db.GetColnamesForClassifier()
        for c in ['TableNumber', 'ImageNumber', 'ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY']:
            assert c not in cols
            
    def test_GetCellDataForClassifier_local(self):
        self.setup_local()
        cellData = self.db.GetCellDataForClassifier((0,1,1))
        assert len(cellData) == 615
        
    def test_ReadExportToDB(self):
        '''Test reading data from Export to Database.'''
        self.setup_local2()
        vals = [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,), (11,), (12,), (13,), (14,), (15,), (16,), (17,), (18,), (19,), (20,)]
        groups = {'Plate+Well': {(u'Week1_22123', u'B05'): [(13,), (14,), (15,), (16,)], (u'Week1_22123', u'B02'): [(1,), (2,), (3,), (4,)], (u'Week1_22123', u'B04'): [(9,), (10,), (11,), (12,)], (u'Week1_22123', u'B06'): [(17,), (18,), (19,), (20,)], (u'Week1_22123', u'B03'): [(5,), (6,), (7,), (8,)]}}, {'Plate+Well': ['Image_Metadata_Plate_DAPI', 'Image_Metadata_Well_DAPI']}
        assert len(self.db.GetAllImageKeys())==20
        assert self.db.GetAllImageKeys() == vals
        assert self.db.GetGroupMaps(True) == groups
        
    def test_CreateMySQLTempTableFromData(self):
        self.setup()
        data = [['A01', 1, 1.],
                ['A02', 1, 2.],
                ['A03', 1, -np.inf],
                ['A04', 1, np.inf],
                ['A04', 1, np.nan],
                ['A04', 1, 100],
                ['A04', 1, 200],
                ]
        colnames = ['well', 'plate', 'vals']
        self.db.CreateTempTableFromData(data, colnames, '__test_table')
        res =  self.db.execute('select * from __test_table')
        assert res==[('A01', 1, 1.0), ('A02', 1, 2.0), ('A03', 1, None), ('A04', 1, None), ('A04', 1, None), ('A04', 1, 100.0), ('A04', 1, 200.0)]
        
    def test_CreateSQLiteTempTableFromData(self):
        self.setup_local()
        data = [['A01', 1, 1.],
                ['A02', 1, 2.],
                ['A03', 1, -np.inf],
                ['A04', 1, np.inf],
                ['A04', 1, np.nan],
                ['A04', 1, 100],
                ['A04', 1, 200],
                ]
        colnames = ['well', 'plate', 'vals']
        self.db.CreateTempTableFromData(data, colnames, '__test_table')
        res =  self.db.execute('select * from __test_table')
        assert res==[('A01', 1, 1.0), ('A02', 1, 2.0), ('A03', 1, None), ('A04', 1, None), ('A04', 1, None), ('A04', 1, 100.0), ('A04', 1, 200.0)]
    
        
        