====================================
II. Installation and getting started
====================================

CPA releases
============

All CellProfiler-Analyst releases can be found `here <http://cellprofileranalyst.org/releases>`_

II.A Mac OS
=============

Copy CellProfiler-Analyst.app to /Applications.

II.B Windows
==============

Run the setup.exe to install CPA and create shortcuts.

II.C Using the example dataset
==============================

Download the CPA example dataset from http://cellprofileranalyst.org/ or `this link <http://d1zymp9ayga15t.cloudfront.net/content/Examplezips/cpa_2.0_example.zip>`_ and unzip it to create the cpa_example directory. This directory contains:

1. example.properties - Configuration file for CPA (see section III).
2. MyTrainingSet.txt - Example training set file to be used in the Classifier (see section V).
3. images/ - Images from the screen used in the example.
4. per_image.csv - Comma Separated Values file for image data. This file was exported by CellProfiler’s ExportToDatabase module.
5. per_object.csv - Comma Separated Values file for object data. This file was exported by CellProfiler’s ExportToDatabase module.
6. example_SETUP.SQL - Used by CPA to create an internal database (SQLite). It can also be used to create a MySQL database. This file was exported by CellProfiler’s ExportToDatabase module.

Run the CPAnalyst file created by the install process above. A dialog will appear asking you to select a properties file. Navigate to the cpa_example directory and select the example.properties file. You’re now ready to experiment with CellProfiler Analyst!
