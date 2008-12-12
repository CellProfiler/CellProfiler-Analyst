# =============================================================================
#
#                       Classifier 2.0 Beta README
#
#   Author: Adam Fraser
#   Developers: Adam Fraser, Thouis R. Jones
#   Copyright 2008, The Broad Institute of MIT and Harvard.
#   CellProfiler.org
#   Distributed under the GPLv2.
#
# =============================================================================


---------------------------------
  I. About Classifier 2.0 Beta
---------------------------------
Classifier was developed at The Broad Institute Imaging Platform and is
distributed under the GNU General Public License version 2. (See LICENSE.txt) 

At this point, Classifier is only tested to run on MacOS 10.4 and 10.5.  It will
soon also be available for Windows users. 


---------------------------------
  II. Requirements
---------------------------------
This software requires access to a MySQL database where per-image and per-object
measurements and metadata are stored, as well as the images used to create the
via the file system or http.  This information is stored in a PROPERTIES FILE
which must be loaded at the application start.  See the example properties files
for more information.  

Classifier was designed to work with data processed by CellProfiler, though any
experiment that measures object features from images should be easily adaptable,
if it stores its data in a similar form. 

IMAGES:
Individual image files are expected to be monochromatic and represent a single
channel.  However, any number of images may be combined by adding a new channel
path and filename column to the per-image table of your database and the
relevant information in the properties file. 

MYSQL TABLES:
Two tables are required: "per_image" and "per_object" (these names can be
changed and set in your properties file). 

PER_IMAGE TABLE:
The per_image table requires 1 column for a _unique_ image ID and 2 columns for
each channel represented in your images:  One column for the image path, and one
column for the image filename (which may include multiple path elements). 

For example, if you took images of cells stained with GFP and Hoechst, you would
have 2 channels and your per_image table would look something like this: 

                          Example_Per_Image_Table
  +------------------------------------------------------------------------+
  | ImgID | GFP_path | GFP_file | Hoechst_path | Hoechst_file | other cols |
  |-------+----------+-----------------------------------------------------+
  |     1 | path     | gfp1.tif |         path | hoechst1.tif | ...        |
  |     2 | path     | gfp2.tif |         path | hoechst2.tif | ...        |
  |                                    ...                                 |
  +------------------------------------------------------------------------+

PER_OBJECT TABLE:
The per-object table requires 4 columns: a foreign key image ID column, a
_unique_ object ID column, a column for the object x-location, and a column for
the object y-location.  The location columns should contain values in pixel
coordinates for where each object falls in it's parent image. 
 
            Example_Per_Object_Table
  +------------------------------------------------+
  | ImgID | ObjID | X_Coord | Y_Coord | other cols |
  |-------+----------+-----------------------------+
  |     1 |     1 |   3.243 | 125.234 | ...        |
  |     1 |     2 |  411.12 |  50.001 | ...        |
  |                        ...                     |
  +------------------------------------------------+


---------------------------------
  III. Getting Started
---------------------------------
Classifier allows you to identify cells or other objects of interest by applying
user-informed machine learning methods to the measurements of the objects.  You
can request (FETCH) object thumbnails (cropped from their original images).  You
may then sort them into classification bins to form a "TRAINING SET." 

Once you have objects sorted into at least two bins of your training set, you
can TRAIN the underlying classifier to start identifying which features
differentiate different classes (RULES) between your object classes
(PHENOTYPES). 

Once you train an initial classifier, you may request objects from any of the
phenotypes classes in your training set.  Classifier will display thumbnails of
what it thinks are objects from the specified phenotype.  You may then refine
the classifier by sorting these objects into their appropriate classification
bins. 

Repeating this process iteratively should yield increasingly accurate rules for
identifying your phenotypes. 

Once you are confident in the classifier rule set, you may score your entire
experiment on a per-image or per-group basis (if you have defined groups in your
properties file).  This will present you with a table of object counts and
enrichment values for each phenotype you defined.  You may then sort by these
columns to find images (or groups) that are enriched or depleted for a
particular phenotype based on counts or enrichment scores. 

Enrichment scores are computed as the log area under the ROC curve for the
posterior versus the prior distribution.  The prior is computed from the full
experiment using a Dirichlet-Multinomial distribution fit to the groups, and the
posterior is computed for each group independently.


---------------------------------
  IV. Other Features
---------------------------------
* Training sets may be saved and loaded from file so you can quit, restart and
  resume training. 
* Enrichment score tables may be saved as a CSV file for loading in Excel or
  other programs. 
* New classifier bins can be added by clicking the "+" button.
* Classifier bins can be renamed by right-clicking on the bin and selecting
  "Rename" from the popup menu. 
* Bins can be removed by holding the alt key and clicking on the bin.
* Double click object thumbnails to show the object in context in the image it
  was drawn from. 
* Right click on thumbnails and classifier bins for other features.
* Ctrl+a: select all tiles in the current bin
* Ctrl+d: deselect all tiles.  XXX not ctrl-shift-A?
* Ctrl+i: invert selection.
* Delete: remove selection from bin.
* Up & down arrows: scroll bin contents.
* Ctrl+1,2,3...: Toggle first,second,third... color channels.
* Image channels may be re-mapped to different colors by using the channel drop
  down menus (these channels are named in your properties file). 
* Double click on the first row in enrichment score tables  to show the image or
  images in that row's group. (Right click for a list of the images from that
  row.) 
* Click on enrichment table column-labels to sort by that column.  Click again
  to reverse the sort. 



---------------------------------
  V. Known Issues
---------------------------------
* "Fetch" may hang when trying to fetch objects of a  particular phenotype if
  none exist in the selected filter group. 
* Color channel menu bullets may fall out of sync with displayed colors when you
  toggle channels on/off with Ctrl+1,2,3... 
* Image & thumbnail scaling has yet to be implemented for high-res images.
* Please report other bugs, issues, or feature requests to the forum at
  cellprofiler.org/forum 
