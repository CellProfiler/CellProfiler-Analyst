# =============================================================================
#
#                 Properties file README for Classifier 2.1
#
# NOTE: Classifier 2 will not read old CPA properties files, nor will CPA read 
#       this properties file format.  The two formats can, however be easily 
#       converted by hand.
#
# This file is an example properties file to help users of Classifier 2 to
# setup your own properties file.  The syntax is simple.  Lines that begin
# with the "#" sign are comments which are ignored by Classifier.  All other
# lines must be in one of one of the following 2 forms:
#
#    property_name  =  value 
#    property_list  =  value1, value2
#
# Optional fields may be left blank:
#
#    optional_property  =
#
# Below, many properties are filled in with example values surrounded by angled
# brackets like <this>.  These MUST BE REPLACED.  Values not flanked by angled
# bracked are suggested guesses.  These values may work as-is, but do read the
# description for each section so you know whether it applies to you. 
#
# =============================================================================

# ======== Database Info ======== 
# Classifier needs to know how to access your database.

db_type    =  mysql
db_port    =  3306
db_host    =  <your_host_name>
db_name    =  <your_database_name>
db_user    =  <your_user_name>
db_passwd  =  <your_password>


# ======== CSV File Info ========
# You may use CSV files for your per-image and per-object tables in place of a
# MySQL database. Classifier will use them to create a SQLite database.
# In this case you must COMMENT OUT THE FIELDS in the Database Info section and
# uncomment the fields below.

#db_type          =   sqlite
#image_csv_file   =  </path/to/per_image.csv>
#object_csv_file  =  </path/to/per_object.csv>


# ======== Database Tables ======== 
image_table   =  <your_per_image_table_name>
object_table  =  <your_per_object_table_name>


# ======== Database Columns ======== 
# Specify the database column names that contain unique IDs for images and 
# objects (and optionally tables).
#
# table_id (OPTIONAL): This field lets Classifier handle multiple tables if 
#          you merge them into one and add a table_number column as a foreign
#          key to your per-image and per-object tables. 
# image_id: must be a foreign key column between your per-image and per-object
#           tables
# object_id: the object key column from your per-object table

table_id    =  <your_table_number_key_column>
image_id    =  <your_image_number_key_column>
object_id   =  <your_object_number_key_column>

# Also specify the column names that contain X and Y coordinates for each 
# object within an image.

cell_x_loc  =  <your_object_x_location_column>
cell_y_loc  =  <your_object_y_location_column>


# ======== Image Path and Filename Columns ========
# Classifier needs to know where to find the images from your experiment.
# Specify the column names from your per-image table that contain the image
# paths and file names here.
#
# Individual image files are expected to be monochromatic and represent a single
# channel. However, any number of images may be combined by adding a new channel
# path and filename column to the per-image table of your database and then 
# adding those column names here.
#
# NOTE: These lists must have equal length!

image_channel_paths  =  <col_containing_dna_stain_image_paths>, <col_containing_actin_stain_image_paths>,
image_channel_files  =  <col_containing_dna_stain_image_filenames>, <col_containing_actin_stain_image_filenames>,

# Give short names for each of the channels (respectively)

image_channel_names   =  <DNA>, <Actin>,

# Specify a default color for each of the channels (respectively)
# Valid colors are: [red, green, blue, magenta, cyan, yellow, gray, none]

image_channel_colors  =  <red>, <green>,


# ======== Image access info ======== 
# Specify for HTTP image access. This address will be prepended to the image 
# path and filename pulled from the database columns listed above when loading
# an image.
#
# Example: If you set image_url_prepend to "http://yourserver.com/" and the
#   path and filename in the database for a given image are "yourpath" and 
#   "file.png"
#   Classifier will try to open "http://yourserver.com/yourpath/file.png"
# 
# Leave blank if images are stored locally.

image_url_prepend  =  <http://yourserver.com>


# ======== Dynamic Groups ========
# OPTIONAL
# Here you can define groupings to choose from when classifier scores your experiment.  (eg: per-well)
# FORMAT:
#   group_XXX  =  MySQL select statement that returns image-keys and group-keys, where XXX will be the name of the group.
# EXAMPLE GROUPS:
#   group_SQL_Well       =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Per_Image_Table.well FROM Per_Image_Table
#   group_SQL_Gene       =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Well_ID_Table.gene FROM Per_Image_Table, Well_ID_Table WHERE Per_Image_Table.well=Well_ID_Table.well
#   group_SQL_Well+Gene  =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Well_ID_Table.well, Well_ID_Table.gene FROM Per_Image_Table, Well_ID_Table WHERE Per_Image_Table.well=Well_ID_Table.well

group_SQL_YourGroupName  =  


# ======== Image Filters ========
# OPTIONAL
# Here you can define image filters to let you select objects from a subset of your experiment when training the classifier.
# FORMAT:
#   filter_SQL_XXX  =  MySQL select statement that returns image keys you wish to filter out, where XXX is the name of the filter.
# EXAMPLE FILTERS:
#   filter_SQL_EMPTY  =  SELECT TableNumber, ImageNumber FROM CPA_per_image, Well_ID_Table WHERE CPA_per_image.well=Well_ID_Table.well AND Well_ID_Table.Gene="EMPTY"
#   filter_SQL_CDKs   =  SELECT TableNumber, ImageNumber FROM CPA_per_image, Well_ID_Table WHERE CPA_per_image.well=Well_ID_Table.well AND Well_ID_Table.Gene REGEXP 'CDK.*'

group_SQL_YourFilterName  =  


# ======== Meta data ======== 
# What are your objects called?
# FORMAT:  object_name  =  singular name, plural name

object_name  =  cell, cells,


# ======== Excluded Columns ======== 
# OPTIONAL
# Classifier uses columns in your per_object table to find rules. It will 
# automatically ignore ID columns defined in table_id, image_id, and object_id 
# as well as any columns that contain non-numeric data.
#
# Here you may list other columns in your per_object table that you wish the 
# classifier to ignore when finding rules.
#
# You may also use regular expressions here to match more general column names.
#
# Example: classifier_ignore_substrings = WellID, Meta_.*, .*_Position
#   This will ignore any column named "WellID", any columns that start with
#   "Meta_", and any columns that end in "_Position".

classifier_ignore_substrings  =  <your_object_x_location_column>, <your_object_y_location_column>, <meta_.*>, 


# ======== Other ======== 
# Classifier will show you square thumbnails of objects cropped from their 
# original images. Specify the thumbnail size here. The approximate maximum 
# diameter of your objects (in pixels) is a good start.

image_tile_size   =  50


# ======== Auto Load Training Set ========
# OPTIONAL
# You may enter the full path to a training set that you would like Classifier
# to automatically load when started.

training_set  =  


# ======== Internal Cache ========
# It shouldn't be necessary to cache your images in the application, but the 
# cache sizes can be set here.
#
# Example: image_buffer_size = 100
#   This will tell Classifier to keep up to 100 images stored in the program 
#   for fast access.

image_buffer_size  =  1
tile_buffer_size   =  1



