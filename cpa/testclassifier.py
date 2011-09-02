import dbconnect
from datatable import DataGrid
from datamodel import DataModel
from imagecontrolpanel import ImageControlPanel
from properties import Properties
from scoredialog import ScoreDialog
import sortbin
from tilecollection import EVT_TILE_UPDATED
from trainingset import TrainingSet
from cStringIO import StringIO
import fastgentleboostingmulticlass
import imagetools
import multiclasssql
import polyafit
import numpy
import os
import wx
from classifier import *


import time
if __name__ == "__main__":
    app = wx.PySimpleApp()

    p = Properties.getInstance()
    db = dbconnect.DBConnect.getInstance()
    dm = DataModel.getInstance()

#    props = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/2007_10_19_Gilliland_LeukemiaScreens_Validation_v2_AllBatches_DuplicatesFiltered_FullBarcode_testSinglePlate.properties'
#    ts = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/trainingvalidation3b.txt'
    props = '../Properties/nirht_area_test.properties'
    ts = '/Users/afraser/Desktop/MyTrainingSet.txt'
    p.LoadFile(props)
    classifier = Classifier(p)
    classifier.Show(True)
    classifier.LoadTrainingSet(ts)
    time.sleep(3)
    classifier.FindRules()
    classifier.ScoreAll()
    
    app.MainLoop()