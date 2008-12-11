# =============================================================================
#
#                       Classifier 2.0 Beta README
#
#   Author: Adam Fraser
#   Developers: Thouis R. Jones, Adam Fraser
#   The Broad Institute of MIT and Harvard.  Copyright 2008
#   www.CellProfiler.org
#
# =============================================================================


---------------------------------
  I. About Classifier 2.0 Beta
---------------------------------
Classifier was developed at The Broad Institute Imaging Platform and is distributed under the GNU General Public License. (See LICENSE.txt)

At this point, Classifier is only tested to run on MacOS 10.4 and 10.5.  It will soon also be available for Windows users.


---------------------------------
  II. Requirements
---------------------------------
This software requires access to a MySQL database where per-image and per-object measurements and metadata are stored, as well as access to a (local or remote) file server where the images will be hosted.  This information is all linked into Classifier by a PROPERTIES FILE which must be loaded at the application start.  See the example properties files for more information.

Classifier was designed to work with data processed by CellProfiler, though any experiment that measures object features from images should be easily adaptable.

IMAGES:
Image files are expected to be monochromatic and represent a single channel.  However, any number of images may be linked adding a new channel path and filename column to the per-image table of your database.

MYSQL TABLES:
Two tables are required: "per-image" and "per-object" (these names can be changed and set in your properties file).

PER-IMAGE TABLE:
The per-image table requires 1 column for a _unique_ image ID and 2 columns for each channel represented in your images:  One column for the image path on the file server, and one column for the image filename.

ie: If you took images of cells stained with GFP and Hoechst, you would have 2 channels and your per-image table would look something like this:

                          Example_Per_Image_Table
  +------------------------------------------------------------------------+
  | ImgID | GFP_path | GFP_file | Hoechst_path | Hoechst_file | other cols |
  |-------+----------+-----------------------------------------------------+
  |     1 | gfp/path | gfp1.tif | hoechst/path | hoechst1.tif | ...        |
  |     2 | gfp/path | gfp2.tif | hoechst/path | hoechst2.tif | ...        |
  |                                    ...                                 |
  +------------------------------------------------------------------------+

PER-OBJECT TABLE:
The per-object table requires only 3 columns: a _unique_ object ID column, a column for the object x-location, and a column for the object y-location.  The location columns should contain values in pixel coordinates for where each object falls in it's parent image.

           Example_Per_Object_Table
  +----------------------------------------+
  | ObjID | X_Coord | Y_Coord | other cols |
  |-------+----------+---------------------+
  |     1 |   3.243 | 125.234 | ...        |
  |     2 |  411.12 |  50.001 | ...        |
  |                ...                     |
  +----------------------------------------+



---------------------------------
  III. Getting Started
---------------------------------
Classifier allows you to identify cells or other objects of interest by applying user-informed machine learning methods to the measurements of the objects.  You can request (FETCH) to see object thumbnails (automatically cropped from their original images) from your image set.  You may then sort them into classification bins to form a "TRAINING SET."

Once you have objects sorted into at least two bins of your training set, you can TRAIN the underlying classifier to start identifying differentiating-features (RULES) between your object classes (PHENOTYPES).

Once you train the classifier, you may request objects from phenotypes defined in your training set.  Classifier will display thumbnails of what it thinks are objects from the specified phenotype.  You may then refine the classifier by sorting these objects into their appropriate class bins.

Repeating this process iteratively should yield increasingly accurate rules for differentiating your phenotypes exactly as you see them.

Once you are confident in the classifier rule set, you may score your entire experiment on a per-image basis (or per-group if you have defined groups in your properties file).  This will present you with a table of object counts and enrichment values for each phenotype you defined.  You may then sort by these columns to find images (or groups of images) that contain a high/low enrichment of a particular phenotype; or a high/low object count of a particular phenotype.



---------------------------------
  IV. Other Features
---------------------------------
* Training sets may be saved and loaded from file so you can pick up where you left off.
* Enrichment score tables may be saved as a CSV file for opening in Excel or other programs.
* Sorting bins can be added by clicking the "+" button.
* Sorting bins can be renamed by right-clicking on the bin and selecting the rename item from the popup menu.
* Sorting bins can be removed by holding the alt key and clicking on the bin.
* Object thumbnails may be double clicked to show the full image they were derived from.
* Right click on object thumbnails and sorting bins for other features.
* Ctrl+a: select all tiles in the current bin
* Ctrl+d: deselect all tiles.
* Ctrl+i: invert selection.
* Delete: remove selection from board.
* Up & down arrows: scroll board contents.
* Ctrl+1,2,3...: Show/hide channels 1,2,3...
* Image channels may be re-mapped to different colors by using the channel drop down menus (these channels are named in your properties file).
* Double click on enrichment table row-labels to show image/images in row group. (Right click for a list of images.)
* Click on enrichment table column-labels to sort by that column.  Click again to reverse the sort.



---------------------------------
  V. Known Issues
---------------------------------
* "Fetch" may hang when trying to fetch classified objects that fall within a certain filter defined in your properties file.
* Color channel menu bullets may fall out of sync with displayed colors when you toggle channels on/off with Ctrl+1,2,3...
* Image & thumbnail scaling has yet to be implemented for high-res images.


