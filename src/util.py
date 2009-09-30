"""
cpa.util

Module for various code that is useful for several projects, even if
it is not used by the CPA application itself.

"""

import numpy as np
import cPickle

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

def unpickle(filename, nobjects=None):
    """Unpickle that can handle numpy arrays.  NOBJECTS is the number
    of objects to unpickle.  If None, all objects in the file will be
    unpickled."""
    f = open(filename)
    def unpickle1():
        o = cPickle.load(f)
        if isinstance(o, np.dtype):
            return np.fromfile(f, dtype=o)
        else:
            return o
    results = []
    while True:
        try:
            results.append(unpickle1())
        except EOFError:
            if nobjects is None:
                break
            elif len(results) < nobjects:
                raise
        if nobjects is not None and len(results) == nobjects:
            break
    f.close()
    return tuple(results)

def unpickle1(filename):
    """Convenience function, returns the first unpickled object directly."""
    return unpickle(filename, 1)[0]

def pickle(filename, *objects):
    """Pickle that can handle numpy arrays."""
    f = open(filename, 'wb')
    for o in objects:
        if isinstance(o, np.ndarray):
            cPickle.dump(o.dtype, f)
            o.tofile(f)
        else:
            cPickle.dump(o, f)
    f.close()
