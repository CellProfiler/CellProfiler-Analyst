=======================
XVII. FAQ
=======================

Q1: I automatically correct images in my CP pipeline and save the corrected images to perform the analysis on them. However CPA opens the uncorrected images. I can't change the settings in the CPA properties file, and the path to the corrected images is not stored in the database (the corrected images are stored in the input folder but they have a different name).
From https://forum.image.sc/t/path-to-aligned-images-in-cpa/16850

A1: In the SaveImages module for the corrected images, check the box near the end of the settings that says "Record the file and path information to the saved image?" That setting is where the path gets input into the database and then into your properties file.