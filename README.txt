# =============================================================================
#
#                       Classifier 2.1 Beta README
#
#   Authors: Adam Fraser, Thouis R. Jones
#   Developers: Adam Fraser, Thouis R. Jones
#   Copyright 2008, The Broad Institute of MIT and Harvard.
#   CellProfiler.org
#   Distributed under the GPLv2.
#
# =============================================================================


---------------------------------
 CONTENTS
 -------------------------------- 
   I. About Classifier 2.1 Beta
  II. Requirements
 III. Getting Started
  IV. Other Features
   V. Known Issues
---------------------------------


---------------------------------
  I. About Classifier 2.1 Beta
---------------------------------
Classifier was developed at The Broad Institute Imaging Platform and is
distributed under the GNU General Public License version 2. (See LICENSE.txt) 

Classifier has been primarily tested on MacOS 10.4 and 10.5, but it has now
been shown to function on Windows XP as well. 


---------------------------------
  II. Requirements
---------------------------------
This software requires access to a MySQL database where per_image and per_
object measurements and metadata are stored. Alternatively, this data may be
loaded from CSV files into a local SQLite3 database. Classifier also requires
access to the images used to create the data tables. The images can be stored 
locally or remotely and accessed via HTTP. This information is stored in a
PROPERTIES FILE which must be loaded at the application start. See the example
properties files for more information. 

Classifier was designed to work with data processed by CellProfiler, though any
experiment that measures object features from images should be easily
adaptable, if it stores its data in a similar form. 

IMAGES:
Individual image files are expected to be monochromatic and represent a single
channel. However, any number of images may be combined by adding a new channel
path and filename column to the per_image table of your database and the
relevant information in the properties file. 

TABLES:
Two tables are required: "per_image" and "per_object" (these names can be
changed and set in your properties file). These can either reside in a MySQL
database or in CSV files which Classifier can load into an SQLite3 database.

PER_IMAGE TABLE:
The per_image table requires 1 column for a _unique_ image ID and 2 columns for
each channel represented in your images:  One column for the image path, and
one column for the image filename (which may include multiple path elements). 

For example, if you took images of cells stained with GFP and Hoechst, you
would have 2 channels and your per_image table would look something like this: 

                          Example_Per_Image_Table
  +------------------------------------------------------------------------+
  | ImgID | GFP_path | GFP_file | Hoechst_path | Hoechst_file | other cols |
  |-------+----------+-----------------------------------------------------+
  |     1 | path     | gfp1.tif | path         | hoechst1.tif | ...        |
  |     2 | path     | gfp2.tif | path         | hoechst2.tif | ...        |
  |                                    ...                                 |
  +------------------------------------------------------------------------+

PER_OBJECT TABLE:
The per_object table requires 4 columns: a foreign key image ID column, a
_unique_ object ID column, a column for the object x-location, and a column for
the object y-location. The location columns should contain values in pixel
coordinates for where each object falls in its parent image. 
 
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
Classifier allows you to identify cells or other objects of interest by
applying user-informed machine learning methods to objects measurements. You
can request (FETCH) object thumbnails (cropped from their original images). You
may then sort them into classification bins to form a "TRAINING SET." 

Once you have objects sorted into at least two bins of your training set, you
can TRAIN the underlying classifier to start identifying which features can be
used to form RULES to differentiate between your object classes (PHENOTYPES). 

Once you train an initial classifier, you may request objects from any of the
phenotypes in your training set. Classifier will display thumbnails of what it
thinks are objects from the specified phenotype. You may then refine the 
classifier by sorting these objects into their appropriate classification bins. 

Repeating this process iteratively should yield increasingly accurate rules for
identifying your phenotypes. 

Once you are confident in the classifier rule set, you may score your entire
experiment on a per_image or per_group basis (if you have defined groups in
your properties file). This will present you with a table of object counts and
enrichment values for each phenotype you defined. You may then sort by these
columns to find images (or groups) that are enriched or depleted for a
particular phenotype based on object counts or enrichment scores. 

Enrichment scores are computed as the log area under the ROC curve for the
posterior versus the prior distribution. The prior is computed from the full
experiment using a Dirichlet-Multinomial distribution fit to the groups, and
the posterior is computed for each group independently.


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
* Bins can be removed by right-clicking on the bin and selecting "Remove Bin"
  from the popup menu.
* Double click object thumbnails to show the object in context in the image it
  was drawn from.
* Right click on thumbnails and classifier bins for other features.
* Ctrl+a: select all tiles in the current bin
* Ctrl+d: deselect all tiles.
* Ctrl+i: invert selection.
* Delete: remove selection from bin.
* Ctrl+1,2,3...: Toggle first,second,third... color channels on and off.
* Image channels may be re-mapped to different colors by using the channel drop
  down menus (these channels are named in your properties file). 
* Double click on the first row in enrichment score tables  to show the image
  or images in that row's group. (Right click for a list of the images from
  that row.) 
* Click on enrichment table column-labels to sort by that column. Click again
  to reverse the sort. 
* Objects of each class may be identified in a particular image by clicking the
  "Score Image" button.
* Full-sized images can be saved as PNG or JPG files by choosing File>Save from
  the menubar or using shortcut Ctrl+S. 
* The brightness and scale of the object tiles may be adjusted by choosing
  Display>ImageControls from the menubar.
* Regular expressions may now be used in defining columns that the classifier
  will ignore in classifier_ignore_substrings in properties files.
* When finding rules, Classifier will now automatically ignore table, image, 
  and object ID columns as well as any columns that contain non-numeric data.
  

---------------------------------
  V. Known Issues
---------------------------------
* Color channel menu bullets may fall out of sync with displayed colors when
  you toggle channels on/off with Ctrl+1,2,3... 
* Linux is not yet supported due to an unresolved error in the drag and drop
  mechanism.
* Please report other bugs, issues, or feature requests to the forum at
  cellprofiler.org/forum 
