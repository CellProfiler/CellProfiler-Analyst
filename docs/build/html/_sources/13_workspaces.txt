================
XIII. Workspaces
================

**Workspaces** in CPA are a way of saving the state of your plots so they can be reopened later
and even applied as a template to new datasets.

Suppose you are performing quality control on a biological screen in which new plates (or
slides) are imaged every week. The way you process and perform quality control on each new
plate is largely the same. For example, you first run a CellProfiler pipeline producing various QC
measures such as focus scores and stain intensities. Then, in CPA, you want to create (for
example) a DNA content histogram and a scatterplot of Measurement_X vs. Measurement_Y
while filtering for your controls. You also display Measurement_Z in P**late Viewer** to look for
wells that may be out of focus. All of these plots can be saved in a workspace file by CPA, and
42
applied to new data later.

To create a workspace, simply open and configure the plots that you wish to save. Then choose
**File > Save workspace** from the CPA file menu. The file that you save will contain configuration
details for all of the currently open plots (Note: Table Viewer and Classifier do not yet support
saving configurations). These same plots can be reopened in CPA by choosing **File > Load
workspace** from the CPA file menu when the same properties file is used. To apply the
workspace to a new dataset, simply open CPA with a different properties file that points to your
other data, then choose **File > Load workspace** from the CPA file menu. CPA will try to apply
the same settings to all of the plots that were open while using your new data.

    **Warning**: If you save a histogram plot of per_image.Measurement_X in a workspace
    and try to open the workspace with a dataset that doesn’t have a Measurement_X
    column in it’s per_image table, CPA will simply use the first measurement in your
    per_image table instead.
