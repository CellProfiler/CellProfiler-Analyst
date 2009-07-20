"""
cpa.util

Module for various code that is useful for several projects, even if
it is not used by the CPA application itself.

"""

import numpy as np

def bin_centers(x):
    """
    Given a list of bin edges, return a list of bin centers.
    Useful primarily when plotting histograms.
    """
    return [(a + b) / 2.0 for a, b in zip(x[:-1], x[1:])]

def heatmap(datax, datay, resolutionx=200, resolutiony=200, logscale=False, 
            extent=False):
    """
    >>> heat = heatmap(DNAvals, pH3vals-DNAvals, 200, 200, logscale=True)
    >>> pylab.imshow(heat[0], origin='lower', extent=heat[1])
    """
    datax = np.array(datax)
    datay = np.array(datay)
    if extent:
        minx = extent[0]
        maxx = extent[1]
        miny = extent[2]
        maxy = extent[3]
        goodx = datax.copy()
        goody = datay.copy()
        goodx[np.nonzero(goodx < minx)] = minx
        goodx[np.nonzero(goodx > maxx)] = maxx
        goody[np.nonzero(goody < miny)] = miny
        goody[np.nonzero(goody > maxy)] = maxy
    else:
        minx = np.min(datax)
        maxx = np.max(datax)
        miny = np.min(datay)
        maxy = np.max(datay)
        goodx = datax
        goody = datay
    bins = [np.linspace(minx, maxx, resolutionx),
            np.linspace(miny, maxy, resolutiony)]
    out = np.histogram2d(datax, datay, bins=bins)[0].transpose()
    if logscale:
        out=out.astype(float)
        out[out>0] = np.log(out[out>0]+1) / np.log(10.0)
    return (out , [minx, maxx, miny, maxy])
