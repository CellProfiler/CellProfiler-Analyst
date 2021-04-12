import cpa.dbconnect
from cpa.datatable import DataGrid
from cpa.datamodel import DataModel
from cpa.imagecontrolpanel import ImageControlPanel
from cpa.properties import Properties
from cpa.scoredialog import ScoreDialog
import cpa.sortbin
from cpa.tilecollection import EVT_TILE_UPDATED
from cpa.trainingset import TrainingSet
from io import StringIO
import cpa.fastgentleboostingmulticlass
import cpa.imagetools
import cpa.multiclasssql
import cpa.polyafit
import numpy
import os
import wx
from cpa.classifier import *


import time
if __name__ == "__main__":
    app = wx.App()

    p = Properties()
    db = dbconnect.DBConnect()
    dm = DataModel()

#    props = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/2007_10_19_Gilliland_LeukemiaScreens_Validation_v2_AllBatches_DuplicatesFiltered_FullBarcode_testSinglePlate.properties'
#    ts = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/trainingvalidation3b.txt'
    props = '../Properties/nirht_area_test.properties'
    ts = '/Users/afraser/Desktop/MyTrainingSet.txt'
    p.LoadFile(props)
    classifier = Classifier(p)
    classifier.Show(True)
    classifier.LoadTrainingSet(ts)
    time.sleep(3)
    classifier.TrainClassifier()
    classifier.ScoreAll()
    
    app.MainLoop()