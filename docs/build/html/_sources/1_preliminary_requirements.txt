================================
I. Preliminary data requirements
================================

CPA requires access to the following data sources:

- An image table and an object table containing measurements and metadata

    These may reside in a MySQL or SQLite database or in a set of comma-separated value (CSV) files. A MySQL database is recommended, though you may need to consult with your local information technology staff to set up a database server. See section II.B for more information. The tables must contain a few datacolumns needed by CellProfiler Analyst to access images and data properly, such as an Image ID column to link the per-image and per-object tables, file path and file name columns to specify where images are stored, and X, Y location columns to specify where each object resides within the image. These configuration details are specified in a properties file. Note: if image classification is specified in the properties file, an object table is not required. See section III.

- The images that were analyzed to generate the above-mentioned Table Viewers

    These can be stored either locally or remotely and accessed via HTTP. The directory structure does not matter as long as the file paths stored in the image table point to the correct images.
    Throughout CPA, the term image is meant to include all image data associated with an analyzed field-of-view. An image in this sense usually includes several individual monochromatic images that show the different wavelengths (channels) as well as images that show outlines of identified objects. You can specify any number of image channels (including, for example, outlines of objects that resulted from image processing) by adding path and filename columns to the image table of your database for each channel.
    CPA currently requires image files to be monochromatic; several individual channels can be combined into a color image for viewing within the software.
    CPA currently supports the following image file types: BMP, CUR, DCX, Cellomics DIB, FLI, FLC, FPX, GBR, GD, GIF, ICO, IM, IMT, IPTC/NAA, JPG/JPEG, MCIDAS, MIC, MSP, PCD, PCX, PIXAR, PNG, PPM, PSD, SGI, SPIDER, TGA, TIF/TIFF, WAL, XBM, XPM, XV Thumbnails.

.. note::
		While designed for high-throughput, image-based biological experiments, CellProfiler Analyst is also useful for the exploration of other multi-dimensional data sets, particularly when data points are linked to images.

I.A Example image table
=======================

The image table requires one column for a unique image ID and a pair of columns for each channel represented in the images: one column for the image path, and one column for the image file name (which may include some part of the path to the image, such as the subdirectory that contains the file). These columns do not need to have specific names; you will indicate which column names correspond to image ID, image path, and image filename when configuring the properties file. The remaining columns can contain measurements and metadata about each image.

.. note::
		While MySQL and SQLite support diverse column names, CPA will not handle column names that contain commas. In general, we advise that you use only alphanumeric characters and underscores in the names of your table columns.

An image table for an experiment involving cells imaged for GFP and Hoechst would have two channels and would look something like this:

.. figure:: static/01_01.jpg
  :align: center

I.B Example  object table
=========================

The object table requires four columns: a foreign key image ID column that corresponds to the image ID in the image table, a unique object ID column, a column for the object x-location, and a column for the object y-location. CPA expects the location columns to correspond to the x-y pixel coordinates of the objects’ centroids; the corresponding column names that are produced by CellProfiler depend on the name of the objects; for example, if nuclei were measured, the column names would be Nuclei_Location_Center_X and Nuclei_Location_Center_Y. Again, these columns do not need to have specific names; you indicate which column names correspond to these functionalities when configuring the properties file. Additional columns in this table typically contain measurements for each object, but are completely up to the user.

.. note::
		While MySQL and SQLite support diverse column names, CPA will not handle column names that contain commas. In general, we advise that you use only alphanumeric characters and underscores in the names of your table columns.

An object table for an experiment involving cells imaged for GFP and Hoechst would have two channels and would look something like this:

.. figure:: static/01_02.jpg
  :align: center
