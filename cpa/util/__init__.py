"""
Module for various code that is useful for several projects, even if
it is not used by the CPA application itself.
"""

import os
import operator
import pickle
from contextlib import contextmanager
import numpy as np
from functools import reduce
# This module should be usable on systems without wx.

def bin_centers(x):
    """
    Given a list of bin edges, return a list of bin centers.
    Useful primarily when plotting histograms.
    """
    return [(a + b) / 2.0 for a, b in zip(x[:-1], x[1:])]

def heatmap(datax, datay, resolutionx=200, resolutiony=200, logscale=False, 
            extent=False):
    """
    > heat = heatmap(DNAvals, pH3vals-DNAvals, 200, 200, logscale=True)
    > pylab.imshow(heat[0], origin='lower', extent=heat[1])
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

def unpickle(file_or_filename, nobjects=None, new=True):
    """
    Unpickle that can handle numpy arrays.  
    
    NOBJECTS is the number of objects to unpickle.  If None, all
    objects in the file will be unpickled.

    new=False => If an object read is a numpy dtype object, a (raw)
    numpy array of that type is assumed to immediately follow the
    dtype objects.

    new=True => If an object read is a numpy dtype object, a (pickled)
    shape tuple and then a (raw) numpy array of that type are assumed to
    immediately follow the dtype objects.
    """
    if hasattr(file_or_filename, 'read'):
        f = file_or_filename
    elif file_or_filename[-3:] == ".gz":
        import gzip
        f = gzip.open(file_or_filename)
    else:
        f = open(file_or_filename)
    def unpickle1():
        o = pickle.load(f)
        if isinstance(o, np.dtype):
            if new:
                shape = pickle.load(f)
            a = np.fromfile(f, dtype=o, count=reduce(operator.mul, shape))
            if new:
                return a.reshape(shape)
            else:
                return a
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
    if not hasattr(file_or_filename, 'read'):
        f.close()
    return tuple(results)

def unpickle1(filename):
    """Convenience function, returns the first unpickled object directly."""
    return unpickle(filename, 1)[0]

def pickle(file_or_filename, *objects):
    """
    Pickle that can handle numpy arrays.

    When encountering a numpy.ndarray in OBJECTS, first pickle the
    dtype, then the shape, then write the raw array data.
    """
    if hasattr(file_or_filename, 'read'):
        f = file_or_filename
    elif file_or_filename[-3:] == ".gz":
        import gzip
        f = gzip.open(file_or_filename, 'wb')
    else:
        f = open(file_or_filename, 'wb')
    for o in objects:
        if isinstance(o, np.ndarray):
            pickle.dump(o.dtype, f)
            pickle.dump(o.shape, f)
            o.tofile(f)
        else:
            pickle.dump(o, f)
    if not hasattr(file_or_filename, 'read'):
        f.close()


class sample(object):
    def __init__(self, n, sequence, length=None):
        """Yield n random elements from the sequence. 
        
        Arguments:
        n        -- a non-negative integer or None
        sequence -- a sequence
        length   -- length of the sequence or None

        if n is None or n >= length, yield the entire sequence.  If
        length is None, use len() to determine it.
        """
        if length is None:
            length = len(sequence)
        if n is None or n > length:
            n = length
        if n < 0:
            raise ValueError(
                "N must be at least 0 and at most the length of the sequence.")
        self.m = 0
        self.i = 0
        self.n = n
        self.length = length
        self.s = iter(sequence)

    def __iter__(self):
        if self.n == self.length:
            return self.s
        else:
            return self

    def __len__(self):
        if self.n == self.length:
            return len(self.s)
        else:
            return self.n

    def __next__(self):
        import random
        while True:
            e = next(self.s)
            i = self.i
            self.i += 1
            u = random.random()
            if (self.length - i) * u < (self.n - self.m):
                self.m += 1
                return e
            if self.m == self.n:
                raise StopIteration

@contextmanager
def replace_atomically(filename):
    tmp = filename + '.tmp'
    with open(tmp, 'w') as f:
        try:
            yield f
            os.rename(tmp, filename)
        except:
            os.remove(tmp)
            raise

def auc(positives, negatives):
    queue = sorted([(v, True) for v in positives] + 
                   [(v, False) for v in negatives])
    auc = 0
    tp = len(positives)
    for v, is_positive in queue:
        if is_positive:
            tp -= 1
        else:
            auc += tp
    n = len(positives) * len(negatives)
    if n:
        return auc * 1.0 / n
    else:
        return np.nan
