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
   V. New Features in 2.1
  VI. Known Issues
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
This software requires access to a MySQL database where per-image and per_
object measurements and metadata are stored. Alternatively, this data may be
loaded from CSV files. Classifier also requires access to the images used to 
create the data tables. The images can be stored locally or remotely and 
accessed via HTTP. This information is stored in a PROPERTIES FILE which must 
be loaded at the application start. See the example properties files for more 
information. 

Classifier was designed to work with data processed by CellProfiler, though any
experiment that measures object features from images should be easily
adaptable, if it stores its data in a similar form. 

IMAGES:
Individual image files are expected to be monochromatic and represent a single
channel. However, any number of images may be combined by adding a new channel
path and filename column to the per-image table of your database and the
relevant information in the properties file. 

TABLES:
Two tables are required: "per-image" and "per_object" (these names can be
changed and set in your properties file). These can either reside in a MySQL
database or in separate CSV (Comma-separated values) files.

per-image TABLE:
The per-image table requires 1 column for a _unique_ image ID and 2 columns for
each channel represented in your images:  One column for the image path, and
one column for the image filename (which may include multiple path elements). 

For example, if you took images of cells stained with GFP and Hoechst, you
would have 2 channels and your per-image table would look something like this: 

                          Example_per-image_Table
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
experiment on a per-image or per-group basis (if you have defined groups in
your properties file). This will present you with a table of object counts and
enrichment values for each phenotype you defined. You may then sort by these
columns to find images (or groups) that are enriched or depleted for a
particular phenotype based on object counts or enrichment scores. 

Enrichment scores are computed as the logit area under the ROC curve for the
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
* Ctrl+A: select all thumbnails in the current bin
* Ctrl+D: deselect all thumbnails.
* Ctrl+I: invert selection.
* Delete: remove selection from bin.
* Ctrl+1,2,3...: Toggle first,second,third... color channels on and off.
* Image channels may be re-mapped to different colors by using the channel drop
  down menus (these channels are named in your properties file). 
* Double click on the first row in enrichment score tables  to show the image
  or images in that row's group. (Right click for a list of the images from
  that row.)
* Click on enrichment table column-labels to sort by that column. Click again
  to reverse the sort.


---------------------------------
  V. New Features in 2.1
---------------------------------
* Classifier now works on Windows!
* When fetching thumbnails, you may now select "image" from the filter combo-
  box to fetch from a particular image.
* When fetching thumbnails, groups defined in your properties file are now also
  shown in the filter combobox. This could help biologists view objects with a
  certain treatment or in a certain well.
* The brightness and scale of the thumbnail images may be adjusted by choosing
  Display>ImageControls from the menubar. These controls were also added to the
  Image Viewer.
* Objects can now be selected in the Image Viewer and dragged into bins for
  training. Shift+click will add/remove from a selection. And Ctrl+A will
  select all objects in the displayed image. Ctrl+D to deselect.
* Full-sized images can be saved from the Image Viewer as PNG or JPG files by 
  choosing File>Save from the menu bar or by Ctrl+S.
* The enrichment table now displays statistics on the currently selected column
  at the bottom of the table.
* The enrichment table now displays separate column names from your database
  that were used to group your results.  
* Objects of each class may be identified in a particular image by clicking the
  "Score Image" button. They may then be shown or hidden by using the 
  class checkboxes.
* Regular expressions may now be used in defining columns that the classifier
  will ignore in classifier_ignore_substrings in properties files.
* Classifier now automatically ignores non-numeric columns in your per_object 
  table, as well as the table ID (if present), image ID, and object ID columns.
* When scoring, you may now choose to score a subset of your experiement by 
  selecting a filter defined in your properties file.
* Areas can now be summed when scoring along with object counts by specifying 
  which column of your per_object table should be used for areas in the 
  properties file field "area_scoring_column".
* Thumbnails are now loaded in the background, so you can fetch thumbnails,
  find rules, load a training set, open images, and score an experiment all at 
  the same time.
* CSV files can now be used in place of a MySQL database. See Properties_README
* Heavier validation of properties files was implemented to help users pinpoint
  properties-related errors quickly and easily.
* Images without objects are now handled properly when scoring.
* Non-consecutive object numbers are now supported. 
* The current properties file is now displayed in the Classifier title bar.
* There is now a progress bar when computing phenotype counts and enrichment
  scores.
* A small dot is now displayed in the center of each thumbnail tile when the
  mouse is hovering over it. This helps to clarify which object in the
  thumbnail needs to be sorted. 
* Linux is now supported although not thoroughly tested.
* Contrast adjustments available from the image control panel.
* Enrichment table now outputs # of images per aggregate-row.
* Improved feedback of scoring progress.
* New properties field check_tables will tell Classifier to check your db
  tables for anomalies such as orphaned objects or missing column indices when
  set to yes.
* PlateMapBrowser tool allows browsing of data in a plate/well view. Images 
  can be opened from any well, and cells from these images can be dragged into 
  Classifier.


---------------------------------
  VI. Known Issues
---------------------------------
* Color channel menu bullets may fall out of sync with displayed colors when
  you toggle channels on/off with Ctrl+1,2,3... 
* Please report other bugs, issues, or feature requests to the forum at
  cellprofiler.org/forum 

  