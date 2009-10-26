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
  IV. PlateMapBrowser
   V. Other Features
  VI. New Features in 2.1
 VII. Known Issues
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
This software requires access to a MySQL database where per-image and per-
object measurements and metadata are stored. Alternatively, this data may be
loaded from CSV files. Classifier also requires access to the images used to 
create the data tables. The images can be stored locally or remotely and 
accessed via HTTP. This information is stored in a PROPERTIES FILE which must 
be loaded at the application start. See the example properties files for more 
information. 

Classifier was designed to work with data processed by CellProfiler, though any
experiment that measures object features from images should be easily
adaptable if it stores its data in a similar form. 

IMAGES:
Individual image files are expected to be monochromatic and represent a single
channel. However, any number of images may be combined by adding a new channel
path and filename column to the per-image table of your database and the
relevant information in the properties file. 

TABLES:
Two tables are required: "per-image" and "per-object" (these names can be
changed and set in your properties file). These can either reside in a MySQL
database or in separate CSV (Comma-separated values) files.

PER-IMAGE TABLE:
The per-image table requires 1 column for a _unique_ image ID and 2 columns for
each channel represented in your images:  One column for the image path, and
one column for the image filename (which may include multiple path elements). 

For example, if you took images of cells stained with GFP and Hoechst, you
would have 2 channels and your per-image table would look something like this: 

                          Example_Per_Image_Table
  +------------------------------------------------------------------------+
  | ImgID | GFP_path | GFP_file | Hoechst_path | Hoechst_file | other cols |
  |-------+----------+-----------------------------------------------------+
  |     1 | path     | gfp1.tif | path         | hoechst1.tif | ...        |
  |     2 | path     | gfp2.tif | path         | hoechst2.tif | ...        |
  |                                    ...                                 |
  +------------------------------------------------------------------------+

PER-OBJECT TABLE:
The per-object table requires 4 columns: a foreign key image ID column, a
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
 IV. PlateMapBrowser
---------------------------------
PlateMapBrowser is a tool for browsing image-based data from 96, 384, and 1536  
well plates (5600 spot microarrays are also supported). The database tables 
and images must be in the same form described above. PlateMapBrowser can be 
launched from the tools menu of Classifier.

In the left hand column, you will find many choice boxes. When you select a
choice from any box, the plate view on the right will be updated. Here is a 
description of what each input is for from top to bottom:

Data source: Database tables are displayed here. Select the table you wish to
  visualize measurements from.
Measurement: Numeric columns from the selected table are displayed here. Select 
  the column you wish to visualize.
Aggregation method: Measurements must be aggregated to a single number for each 
  well so they may be represented by a color. For example, if one is viewing a 
  cell_count column in their per_image table, one might like to sum the counts 
  from each image within a well to get the total cell count per-well. For this 
  case the "sum" item should be selected.
Color map: Each value that is computed for the wells is mapped to a color via a 
  color map. The currently selected color map is represented in a bar beneath 
  the plate maps.
Well shape: Mostly for presentation purposes, you may select from different 
  well shapes.
Number of plates: Multiple plates may be viewed at once by typing a number here 
  and pressing ENTER.

The color bar axis at the bottom of the window shows how aggregated values of 
the selected measurement column map to colors in the plate map view. The 
numbers at the far left and right of the axis represent the min and max values 
found across all plates. The value range of the current plate is represented by 
where the color bar stops and a thin black line begins. One may also rescale or 
clip the color bar by dragging the handles found at the far ends of the bar. To 
change the mode from rescaling to clipping, right click on the bar and select 
the "value bracketing: CLIP" choice. This can be reversed in the same manner. 
Likewise, the clipping handles can be reset to the ends of the axis by right 
clicking and selecting "reset sliders."

The rest of the window displays the plate map view(s). Above each is a choice 
box that controls which plate is being represented. Holding the cursor over a 
particular well will cause a tooltip to display with the aggregate value at 
that well. Right-clickong on a well will display a list of images numbers of 
the images taken in that well. Clicking on a number will open that image in the 
ImageViewer. Double-clicking on a well will open all images from that well at 
once in ImageViewers.


---------------------------------
  V. Other Features
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
 VI. New Features in 2.1
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
  class checkboxes. Object classes may also be represented by colored squares
  or by numbers. This setting can be found in the "View" menu.
* Regular expressions may now be used in defining columns that the classifier
  will ignore in classifier_ignore_substrings in properties files.
* Classifier now automatically ignores non-numeric columns in your per-object 
  table, as well as the table ID (if present), image ID, and object ID columns.
* When scoring, you may now choose to score a subset of your experiement by 
  selecting a filter defined in your properties file.
* Areas can now be summed when scoring along with object counts by specifying 
  which column of your per-object table should be used for areas in the 
  properties file field "area_scoring_column".
* Thumbnails are now loaded in the background, so you can fetch thumbnails,
  find rules, load a training set, open images, and score an experiment all at 
  the same time.
* CSV files can now be used in place of a MySQL database. See Properties_README
* Data from CellProfiler's ExportToDatabase module can now be loaded directly.
  See Properties_README
* SQLite databases are now also supported. See Properties_README
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
  Classifier. This can be launched from Tools > Plate Map Browser
* Total object counts are now reported along with per-class object counts


---------------------------------
  VI. Known Issues
---------------------------------
* Per-well csv data can't be loaded into PlateMapBrowser if the plate and well 
  columns don't match the corresponding columns in the image table. This may 
  happen when a group is defined in the properties file that selects columns 
  using the sql 'SELECT x AS y' construct. When grouping scores in such a way, 
  the column x will appear as y, and can not be matched back to the database.
* If multiple PlateMapBrowsers are open, only the most recent one will be 
  updated with an enrichment table if one is generated.
* Please report other bugs, issues, or feature requests to the forum at
  cellprofiler.org/forum 