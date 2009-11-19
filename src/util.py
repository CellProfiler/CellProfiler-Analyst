"""
Module for various code that is useful for several projects, even if
it is not used by the CPA application itself.
"""

import operator
import cPickle
import numpy as np
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
    if isinstance(file_or_filename, file):
        f = file_or_filename
    elif file_or_filename[-3:] == ".gz":
        import gzip
        f = gzip.open(file_or_filename)
    else:
        f = open(file_or_filename)
    def unpickle1():
        o = cPickle.load(f)
        if isinstance(o, np.dtype):
            if new:
                shape = cPickle.load(f)
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
    if not isinstance(file_or_filename, file):
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
    if isinstance(file_or_filename, file):
        f = file_or_filename
    elif file_or_filename[-3:] == ".gz":
        import gzip
        f = gzip.open(file_or_filename, 'wb')
    else:
        f = open(file_or_filename, 'wb')
    for o in objects:
        if isinstance(o, np.ndarray):
            cPickle.dump(o.dtype, f)
            cPickle.dump(o.shape, f)
            o.tofile(f)
        else:
            cPickle.dump(o, f)
    if not isinstance(file_or_filename, file):
        f.close()



# Tools for retrieving the icons

import base64
import sys
from cStringIO import StringIO
import wx

class EmbeddedImage(object):
    ''' Simple way to store and retrieve b64 encoded images. '''
    def __init__(self, data64):
        self.data64 = data64
        
    def get_image(self):
        ''' returns a wx.Image '''
        data = base64.b64decode(self.data64)
        stream = StringIO(data)
        return wx.ImageFromStream(stream) 

    def get_bitmap(self):
        ''' returns a wx.Bitmap '''
        return wx.BitmapFromImage(self.get_image())
    

def get_cpa_image():
    """The CellProfiler Analyst icon as a wx.Image"""
    data64 = ('iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAACXBIWXMAAAsTAAALEwEAmpwYAAAKT2lDQ1BQaG90b3Nob3AgSUNDIHByb2ZpbGUAAHjanVNnVFPpFj333vRCS4iAlEtvUhUIIFJCi4AUkSYqIQkQSoghodkVUcERRUUEG8igiAOOjoCMFVEsDIoK2AfkIaKOg6OIisr74Xuja9a89+bN/rXXPues852zzwfACAyWSDNRNYAMqUIeEeCDx8TG4eQuQIEKJHAAEAizZCFz/SMBAPh+PDwrIsAHvgABeNMLCADATZvAMByH/w/qQplcAYCEAcB0kThLCIAUAEB6jkKmAEBGAYCdmCZTAKAEAGDLY2LjAFAtAGAnf+bTAICd+Jl7AQBblCEVAaCRACATZYhEAGg7AKzPVopFAFgwABRmS8Q5ANgtADBJV2ZIALC3AMDOEAuyAAgMADBRiIUpAAR7AGDIIyN4AISZABRG8lc88SuuEOcqAAB4mbI8uSQ5RYFbCC1xB1dXLh4ozkkXKxQ2YQJhmkAuwnmZGTKBNA/g88wAAKCRFRHgg/P9eM4Ors7ONo62Dl8t6r8G/yJiYuP+5c+rcEAAAOF0ftH+LC+zGoA7BoBt/qIl7gRoXgugdfeLZrIPQLUAoOnaV/Nw+H48PEWhkLnZ2eXk5NhKxEJbYcpXff5nwl/AV/1s+X48/Pf14L7iJIEyXYFHBPjgwsz0TKUcz5IJhGLc5o9H/LcL//wd0yLESWK5WCoU41EScY5EmozzMqUiiUKSKcUl0v9k4t8s+wM+3zUAsGo+AXuRLahdYwP2SycQWHTA4vcAAPK7b8HUKAgDgGiD4c93/+8//UegJQCAZkmScQAAXkQkLlTKsz/HCAAARKCBKrBBG/TBGCzABhzBBdzBC/xgNoRCJMTCQhBCCmSAHHJgKayCQiiGzbAdKmAv1EAdNMBRaIaTcA4uwlW4Dj1wD/phCJ7BKLyBCQRByAgTYSHaiAFiilgjjggXmYX4IcFIBBKLJCDJiBRRIkuRNUgxUopUIFVIHfI9cgI5h1xGupE7yAAygvyGvEcxlIGyUT3UDLVDuag3GoRGogvQZHQxmo8WoJvQcrQaPYw2oefQq2gP2o8+Q8cwwOgYBzPEbDAuxsNCsTgsCZNjy7EirAyrxhqwVqwDu4n1Y8+xdwQSgUXACTYEd0IgYR5BSFhMWE7YSKggHCQ0EdoJNwkDhFHCJyKTqEu0JroR+cQYYjIxh1hILCPWEo8TLxB7iEPENyQSiUMyJ7mQAkmxpFTSEtJG0m5SI+ksqZs0SBojk8naZGuyBzmULCAryIXkneTD5DPkG+Qh8lsKnWJAcaT4U+IoUspqShnlEOU05QZlmDJBVaOaUt2ooVQRNY9aQq2htlKvUYeoEzR1mjnNgxZJS6WtopXTGmgXaPdpr+h0uhHdlR5Ol9BX0svpR+iX6AP0dwwNhhWDx4hnKBmbGAcYZxl3GK+YTKYZ04sZx1QwNzHrmOeZD5lvVVgqtip8FZHKCpVKlSaVGyovVKmqpqreqgtV81XLVI+pXlN9rkZVM1PjqQnUlqtVqp1Q61MbU2epO6iHqmeob1Q/pH5Z/YkGWcNMw09DpFGgsV/jvMYgC2MZs3gsIWsNq4Z1gTXEJrHN2Xx2KruY/R27iz2qqaE5QzNKM1ezUvOUZj8H45hx+Jx0TgnnKKeX836K3hTvKeIpG6Y0TLkxZVxrqpaXllirSKtRq0frvTau7aedpr1Fu1n7gQ5Bx0onXCdHZ4/OBZ3nU9lT3acKpxZNPTr1ri6qa6UbobtEd79up+6Ynr5egJ5Mb6feeb3n+hx9L/1U/W36p/VHDFgGswwkBtsMzhg8xTVxbzwdL8fb8VFDXcNAQ6VhlWGX4YSRudE8o9VGjUYPjGnGXOMk423GbcajJgYmISZLTepN7ppSTbmmKaY7TDtMx83MzaLN1pk1mz0x1zLnm+eb15vft2BaeFostqi2uGVJsuRaplnutrxuhVo5WaVYVVpds0atna0l1rutu6cRp7lOk06rntZnw7Dxtsm2qbcZsOXYBtuutm22fWFnYhdnt8Wuw+6TvZN9un2N/T0HDYfZDqsdWh1+c7RyFDpWOt6azpzuP33F9JbpL2dYzxDP2DPjthPLKcRpnVOb00dnF2e5c4PziIuJS4LLLpc+Lpsbxt3IveRKdPVxXeF60vWdm7Obwu2o26/uNu5p7ofcn8w0nymeWTNz0MPIQ+BR5dE/C5+VMGvfrH5PQ0+BZ7XnIy9jL5FXrdewt6V3qvdh7xc+9j5yn+M+4zw33jLeWV/MN8C3yLfLT8Nvnl+F30N/I/9k/3r/0QCngCUBZwOJgUGBWwL7+Hp8Ib+OPzrbZfay2e1BjKC5QRVBj4KtguXBrSFoyOyQrSH355jOkc5pDoVQfujW0Adh5mGLw34MJ4WHhVeGP45wiFga'
    '0TGXNXfR3ENz30T6RJZE3ptnMU85ry1KNSo+qi5qPNo3ujS6P8YuZlnM1VidWElsSxw5LiquNm5svt/87fOH4p3iC+N7F5gvyF1weaHOwvSFpxapLhIsOpZATIhOOJTwQRAqqBaMJfITdyWOCnnCHcJnIi/RNtGI2ENcKh5O8kgqTXqS7JG8NXkkxTOlLOW5hCepkLxMDUzdmzqeFpp2IG0yPTq9MYOSkZBxQqohTZO2Z+pn5mZ2y6xlhbL+xW6Lty8elQfJa7OQrAVZLQq2QqboVFoo1yoHsmdlV2a/zYnKOZarnivN7cyzytuQN5zvn//tEsIS4ZK2pYZLVy0dWOa9rGo5sjxxedsK4xUFK4ZWBqw8uIq2Km3VT6vtV5eufr0mek1rgV7ByoLBtQFr6wtVCuWFfevc1+1dT1gvWd+1YfqGnRs+FYmKrhTbF5cVf9go3HjlG4dvyr+Z3JS0qavEuWTPZtJm6ebeLZ5bDpaql+aXDm4N2dq0Dd9WtO319kXbL5fNKNu7g7ZDuaO/PLi8ZafJzs07P1SkVPRU+lQ27tLdtWHX+G7R7ht7vPY07NXbW7z3/T7JvttVAVVN1WbVZftJ+7P3P66Jqun4lvttXa1ObXHtxwPSA/0HIw6217nU1R3SPVRSj9Yr60cOxx++/p3vdy0NNg1VjZzG4iNwRHnk6fcJ3/ceDTradox7rOEH0x92HWcdL2pCmvKaRptTmvtbYlu6T8w+0dbq3nr8R9sfD5w0PFl5SvNUyWna6YLTk2fyz4ydlZ19fi753GDborZ752PO32oPb++6EHTh0kX/i+c7vDvOXPK4dPKy2+UTV7hXmq86X23qdOo8/pPTT8e7nLuarrlca7nuer21e2b36RueN87d9L158Rb/1tWeOT3dvfN6b/fF9/XfFt1+cif9zsu72Xcn7q28T7xf9EDtQdlD3YfVP1v+3Njv3H9qwHeg89HcR/cGhYPP/pH1jw9DBY+Zj8uGDYbrnjg+OTniP3L96fynQ89kzyaeF/6i/suuFxYvfvjV69fO0ZjRoZfyl5O/bXyl/erA6xmv28bCxh6+yXgzMV70VvvtwXfcdx3vo98PT+R8IH8o/2j5sfVT0Kf7kxmTk/8EA5jz/GMzLdsAAAAgY0hSTQAAeiUAAICDAAD5/wAAgOkAAHUwAADqYAAAOpgAABdvkl/FRgAAKDhJREFUeNrsnXmcHVWZ97+nqu7aa1bCGnbQgRZkXwQchYCoM/q6vKOOos7gizLqOKOv0iPgEkXGGXUcxuXFDV5GEJEREGQZZEkIgQRCE5YQCFmAzkrS6fRdquqcM3+cc6rq3r6dREkn6U5Xf+pzl7p9l/r9nuf5Pc95zimhtWasb0IId/dHwGeB6nj4XTvl3I0zAmigGxiYIMAEASbQnSDAxLZdBMicwLG+JQTYUwB8rUSfIMAeToYJAkwQYIIAEwQQgvLsvlH5UrV/fefbdOXVQumf5tw8Wj+80tszjACj9Xt2ly3zm18TAYJR/pKnAr+z968C/g6gPLtvQqLvJps3yu//dOb+p4CfASdWenvExKnfMwgwACwDEK/7S4QQHwEeBi6aIMGeQQCAJUJ4cOrfwllfxS+0IRBXAd+v9PYcMEGE8U+Al12WMeOjF8Bn74XJM/E9/1PACuDvJ0gwTglgxd7zANSrlLtKHHrG4ezz/bmo917jvMG/AD+r9PacMEGE8ekBVgMwtIlCIUdnZ5np+0zikA+eS/7LD8Hr34XvBx8BHgG+MkGC8UeADVpr2NQPQCEf0NVRYuqUDg4+4SAO+MoPUB+5Gb99Kp7wvgzimUpvz6cniDCOCAAaNr9kPlAI2j3oKuTo7iozeWoHh737NLqufBh93nfxix1HCCG+B8yp9PZ8aIIIY58Ag2ggHCBbqMp50B74dLYXmTypnf0On8HBn/gAxa8+BCd+Gj9fPlUIcS0wr9Lb85EJIoxdAlQACLegtUZlWJDzoCgExUKOzo4Skya1c+AbDuDAL/SS650LPR/Gz5dPEkL8HFhY6e3520pvTzAB29gigNmUTD9UmN2RoCSg6Hu0lfKGCFM6OOjEg5n55SvJXzoPjr8Iv9B2rBDej4Go0ttzeaW3Z/oEfK992xnWtF11fx9ACEQ+wPc98jmfQiGg+MaZVI+4jA3LP8XQ7b/Bn/9tdG3LZVrJyyq9Pddgysv3TUA5RgjgZYaePQFKg2+fktp8Ie0JCHzafI9cLqBQyFFqK1A76EIG3/8BXp3zOOKWi/Eqr35YxdGHNfoF4KcTcO6eIaAdgGLXNj/Yt7dCCHxP4HvGE5RLedrbi3R2tzHtgCkc+K4zmP79R+FzD8DR/xu/2H6I5/mz7b//CvhwpbenawLe3cMDGFy9AkIIttZ74onUX8RC4HoVPA9ygY/veeRyPoVCjmK5QLmzRP2Yf2Fo/eUMzF0AN3wQP1c8R8XhOVorKr09twM3AL8tz+4bmIB71'
    'xCgGwG0z0jAb2n99pgaQTE4IgSOT17OkKGYo9iWp2vvt7LiBgj+4S7CRx/Ee+R7iOrA25SM3mbJcCdwN/Cb8uy+Fyeg33kEKIGAYiee5yXtZypr9VsB3oGf7XYx7+O8gyCX84kLJsuY8Wf7IN/wUaIPfYiNy9ah5tyBt+D7iNrmWToOZ2mtvl3p7VkO3AjcC9xfnt1XnSDA6G37CiHQUw9EiPQDs15ANYUBqR3w4CEaagciEyaEMGQARS5n3rlULqCLJaJinmJPkfjIjxF+8K8ZWLmBaNFCWPhD/PVLDiSuf15J+XmNptLbM9dmEnOAOeXZfVsmCLDjtslCCHTXVAsWw7KAkcRg1OAFoLnlTWR0gmOF53t4OZNKSukjCwH5Up5SZxF5xAzid82iuqnK4OIX4PH/wlt2O2Lo1dO0DE/TSmEJ8SgwH1gILCzP7ntyggB/+rY3eHiTuhEiBTdx/Wzd9YPOWLxIicPITZCpZzC3QaBRykdKhYpzFNoKdOx1LPKMHmTUy2D/JupLl8HiO/CW3YGobDwBWT9BKQlaU+ntCR0ZgCft7fPjQVjuDAJMw/MpdJdTUDJx37MkyNYEmr2CJ0QD4Nkw0Jo0jWQAkegP7Xv4SqOkRhcUUioKbdORM6eg3nwcKr6EobWDVF9aC8/Og+X/jb9mUZ6ofgoqOkUrZb+HptLbsw5Ygul9fBLT+7AOeHqs6IqdQYADRZCj2FXC88R2ib6sDtjW1io0jCQes9mEOSbwAg+tQOUkWoOSinw5T+d+k1DHH4pWHyKux1Q3bKH+0mpY/gQsvw+x/mm86qZpxOE0dHy6Cx/uy9i27YVA1RJkHbDSfo2XcX0S8HJ5dt/q8UyA/bVfoNhZxPe8lhYO25cBZMH2hEA2iEOxVWK4442aweWlGg8frTWe74HWKKVRUqGUJlfKUWgvoPabhDrhCJR8D1pqompIbWMFuW49rHwKVj8Jm1fAq0vw60Og4uNQErQ8XWtDDu1cl06LpC16/LNkafxdQf7q0lcW/KRJIu2eBKj09uSBmeTLFNuKeF6aAnpsWwMEQLyTLEF4gErJ5nkCITyE0mglEJ6HpxTaEUNq/LxPvr2A3qcbffTBKPl2VCzRWqOlpr5xCBnGiDWvwOBa2LgKZAibV8FQP6gQKuvwqptAKUAhDFGmAdO0kmgtQSu0MmdKx+Fx1ctPLABXAZLtHGvZVR7gYIFATe8hyHkJAbYF/A4HdythYqRteOgAbMrpYeoQShrPIpGAh1ASz/dQUoHQFLrKKKVg0mEoeQjok81vl2mo0M4dZj5P1UMYHEiZ2f8C3P5pd/gSHdX+02Ind/cQcBBCwN4n4vu+OVk6FYHZrVVYiNm+6U6tYv1rJ00m9HgCvQ1RojOAaq1TPK3H0FKjrQfRUplda4RWIJXxANqaRRxBoYQuFBErl8Kd/+A+5nfAXKADqNkwIHdnAvyZJwTq0OPxfc8M8GQ0QCtBKPWfrhF29ObeNmulBmASkJVUxgnr9HmU2ZXLGLQBX0Uyc1wiotiALqW9jTPxCBM6br8YZIStS/yXFS6xBV7t7h7g9Xg5CvvNwPe9xAP425EJNMf+eKjCmnvuo7ZiKfXlTwCQ3/8o8gcdQdcpJxF0dGwTyKy1JmBtZwhoeGiJYEC3Fp55rKUF31q6kjolkQUfqYaDLxUEAeQLxgv89kKoVdDwFHArsAFYD2wZEyIQOJpcgba9OvH9bY88O+vP+rR1C5/glR9dSu2puzllv1M4svNIDplyNFEU8eyTi1ny4E30/Usfesq+ViTFLUHftusmsdaG49alZ4njAHfWr7OPXQjIgi9VSg6tEc7lO/CtwEvAL5fh3quhOoBGLwF+DTxn6wz9wKCLkLstASq9PT5wPIV22qe04/te8mEunPqiEXwyAS2q1lj69S8RPPwrvnveN3jTx79LubOMsHEjrsdE1Yh6pc7QhiEWPdnHx/s/yrPvPZBJ536RGRf/I/hBk9XrP44U2dc7969UGgKUtqrfkkIqVKwyhGiM9yiNiOPGeO/AFx74gYn7c25ALPo5SutlwG+AZ23B6WVg845Q/7QYk9nh8V8gUPueTr6Yw3cpYFO8d7vSENljg6/089yln+Udrw4y75/n8c73vZOpM6dS7CiSK+ZMvT/wyJVylLvLTJk5hdPffCoAP5v1M173xAM8ff4U1v/y+j9O9WcAT+K/AzoLqlI2FTQWrmJpgc6EBKv0EwJIZVy/Usa9x1FKAq1MhlEqIZ55GLHgKpQ59pAF/zkL/iAgd+T0+tEMAScKz0O/7m34vtcwEJQlgSsBy0zsX/adr/CpYG8u/sLFFMqF5KQqa2EODBlJZCSN1VnEDj36UGbvN5sHF87h2zd8gVeee4i9LvlXVxNuiP9Z999KHzjBp6TKCD6dfI8suO6xAz8lhUoFX0PakwFfeFAowYa18IdLUUYM/gF40IL/knP7O3pthdH0AG8SXkD+qK'
    'MJAj9pBpFNeUsz+M9c+nlOW72GT37skxTaCg1WmFTzVCqqtNbEUYwMzbvIWNI+uZ3Tjz2NK3quZP+nF9L/tb+j9uKqxvQMthn7VdblK5Vx9Tp187FMHo8EfiL4nOVLq/4d+PkColiA+VdDWAVYBNwCLLXgDwDRaCysMZoEOJl8ic59JxEEJgPI2oBsIkMMbHjyaar3/ZhvXfgtA35GqYtM8UA0FxKUtU5AhpKwEhLkAw5/3aF86bgvcdRzy1n5d29g6JHHWuuBViIvSd+0tfo0j1exNB4ojBPFv1XwZZwC71I9+33xPHShiJ7zK3j+LjT6eeAmK/hWAK8C4WitqjIqBKj09kwWiMN11wG0TSqbEGCtN25K8eJMweflH36Vy8+6nEkzJpniSzYmZ9V4xvqTwotVkTKWxGFMWA2RsWTK9ClccPhHOK3zTbzytbOpLH52uPJvkRpmc31HBuP6m8CPpcnvW4EfWcClTIWfVo0xp1BCrFyKWPADtHl+jgX/RZvy1UdzSZ3R8gCnIgT6iHeTK+SS+J8FNEsErTW1TQPUFt3KOaedk7j+VJyNoNB1Gg6yzyulkLEkqkeEtZBp06fxF/u9g6PyR7Ppl98kXNXf0vVnCZVV/So276es3pBxCniiSyz4KpYp+M7ty+x9lVp/kEcHAdzxWXRcc6JvHmZVlTVApTy7T46ilx41Apzp+QEcezZB4CcZQCv3q6zQeum665h18Cy6pnclLrjROhv3LPjKumZTZ08VehzFhPWQeq3OPtP34e0zzqf92UfY9LOvN4CfWLrzJqpRdMqoBfhKtRSDQisDvov3KhP/lTJVPS1Nzl8qIebdCLVBNDwD3Ay8ALziFP9oj5OMFgHOJVdk0uF7JfE/dauNRFB2H5xzLecccg5BIUitPmvhStt6egYgZfYGzyDTY1JKoigiDEOiKOKgGQdxdvlsqo/fxIbvXtoyK3AaIAE/lsbSHfiRakz7kiwgY/kuxVMK4jit9TvrF74p+Kx8DrHwh87132MtfxWwcTTj/qgSoNLbM0MgjlKTD6VjaofNAEQCdJYIMpMPVlc9xaH7HGrH4xstOcnBVeNjA4BGRSoRge41MpIpSaQijELCKOTgyQczSU9i8wM/YODXv0rAVxlV3wi+zfUzeX5i8SoFX8RxCr4Te3FsrD2sm+ejalrxK5bgkR+g4zrAA1b5L98ZcX+0PcBbEAKO/muCvN8wBGzSPt1EBhP/c0rRVmpL3HjWDSf3Y9XgAaQDyx5z/ytjmXgAJRWxjInjmCiOaC+2845J7yAv8rz6y4uR9XpaV4gbaw1Jbp8Rd0b02ddEMgU/q/STeB8Z8O2YPgC5AEptMP9meOVxtKnw3WKtf7Wt80t20jYaBDjf83PkTz6TXC5oEIC6SXC5+F9Z9QqTc5Px8BLLlZFMrFzGMrXouGnPWLnLApRUxHGMlBKpDBliGSOVJJIRB005iHOL5yKEYNNVl2cqfa3AbyrxutdFhhQijlMLj0OI6uZxNhTEoSFGkIdcATatRzzy7871P2gV/8vAptHK93cKAWz9/68odTLpwKkEgZ+kf87tZ2Otux9vqVCkaCp7GauWkUnpshU/GZvXxFGcEiIyz7sQ4F6jtSaOjfU7ImitkUpy5NQjKVFmy7yfEr64aliVMcn5VRrrnRZw4KOse5cxhKF18xZ4FaXAu6pfvgDtHbDgF071z8esjbTSjvTVd/YqqjvaA5wqhEAd+g6K7QUrAJvKrhkiJEWhWhVP+ElFL65nQM/EcxeTZWjcsAxlAraM0kqgs/7k1lp/ds8FOc4tz8IXPkM3faep3p+J+5EDXprnrNunXodq1QAc1Y27j+LU3TvgHfh+YMq9ix9EPHc72lT4brZxfzUwxM5tlBoVArzH8wL0mR8jyBv3rzXDUsDmXQQ56rpOdbBKXI8T0GWUIUOYPo7rcQp8hgSA8Rj2cRRFhFGIVIYEya7M7WFTDqNIicrjNxBv3JyOOcQZa1cqBT+M0VGEcNbuwE/cvQU/Cm36J83zYFx/rgBzv4Eyi2XMt+C7Um+4K9ZQ3sEEEO+m2MHU1+9DLhck9f+WeXzGGwTdXQyqzWwZ2GKGeWtRo9uPWoBvgY/D2Ox2sMW5/FjGRFE0LP7HKja3MkZrzTmlsxFCUL3pqgZXn7j8MDZEsOA3KP1kaFemsT4K7WMLvu9BLg/lDnj011CvAiy2gz0rreqv7qoFtL0dGP+PF4L91Mw/p9xdHpb/Z8vuLgV02UBh+lS2xFtY9+o6wkqYAB3XDbguLDhvENcN4O64210IcNbvLN55AKltCNCSWMWEMmRm90yKFKnO+xGyUmsgnQNfhrFx+0mBJ7T5fZQ+lnGj1TuPYMu9bH4V8fhPnfC729b5+3dWwWdneIAPeF4Af34xuUKQdAA5kKXSDaBnPUOuuwuJx/INK6kN1hpI4MCP6pG5b118An5k9zD1AFEUEcexEYRKNpLA3kb'
    'KeAMhBCeJkwBB+NA9ibW7yl+i9kOr8OMwTfEc+NkKX1RLPYDwIV+Ctk5Y9J9O+M3DzCJ6yar+cFcunx9kLPi1vI8P/D3FDqa+YWZS/BnWVbOVZoziXoeyZOBZNm/YTFAMQIPwTTeujGRS7lWxSkmQsf4oMrE2iiLjAeImD6DixPo1JhOQ1vBmds0k2OQTLfgFuWPPGlYDaIj5rqSbrfZpO+qnwnSs3/MgyEGxHZYtQiy9AwVrMY2dKzH3K4B6jec+DcB/5JVftNY7rCHkLUII1JHvpdhRJAj8BvCzX6xVs6XWmsKRZ/H8vPtYs2oNbV1tyf9lO2xcJuAIENUjA349IgpTAgQqGC78nPizGkBphdJmOld3sZsceaovLcKv1VAiMOBHtsiTVPdUo9KPwoz4k6niB2P9hTZo64BFP0GbYWCX8rnWrohdvVlAVpBU3yf2PWT/DzMv4bVfNGoysMHr2pvp35tP59R2isX8dnUBZ7MBWa/z1PlTOK90PhfN+gTtk9rJF/PpCJ9SSSjIuv04MrdhPeSCORdwZc+VeMojiiPqUZ1QhsTSCL5QhkkKKLUJBx4epVyJlQMr+X30e7xjPoZ+y98YxR+Gtspnrd5ZfxzavL+WWn1mHUSCHLRNgil7w9VvR4cVgGswDZ5PWvFXYwc1dr4W498RIeCjnuejz76CfDmP7/vJMO/WeJUdFQQQuRxtR5xJ3/N9LF++nEOCQ9BKJ1OtHAEaVH5kUr6wbgZ6nAj0tEcYh0boWfCd+5dKolBGC2hNpCMCGdBV7MKLPPz+RYSx7eFzcX4k8OMmD+6EX64I7d2w8LfmdQb0hzLl3nBXgz9MBP6pV9mq9L7hkyLfRucZJ+Pb3r+sZf8xXqDz/E+z+rvvZ/6L89lr+l6Gobkg0QFJlc8SwN3WwzqRBSOUIb7yk7jv1H4ko4YUUGudZAGximnLteHjowdWpnHfib1m8F2a1wr8IGdiv1bw2I9c2ne/Vf3rXMXvtV7VbEddNcx7jV/iL4TgYPX691Oe3EaQa1T/27cbb6GUoustbyaWEbcN/I41a9cwNDhEvVonqkfUa3XqtTpRaO6HYUg9rCfgOwJEcUQYp67eZQFKq2HgK60SUviej4eHDgfT4dyobsu52XRPualajeC7LVe0ad8t5v/hMTvU+wqj2Ny5q+oAF3m5IsF5n7CtXyIZ5XN7Wvtv3NPXqHRwCMHkt3+ZQTazcMVChrYMURmqUKvWEtBrtRpRFKWNHhb8MLYhwKp9RwIHejYVdOBrrRMtIBAEBMSylsZ9SNu3XLqnQuyc/3TPxv5CG1SGoO9atxbA7bbJY51t8VLsRpv3Gqz/LIGYpQ44nSmHTcfzvZbW77p2mvdmorjnuj9wIVJLbt54MxsGNlCtVBPww3pobiNzW4/qyZ54AJl6AOf+HeimA0kl3kBqmRBBaUUB24s4NJCmdVqm5d3mCl9DEu6DlzfW33cTmEaPeZjW7n5n/exmm/earD/Iod9+GUEhwA+8BlC3ZflSqoz16+R/vfYy3WddzCBbWLhyIUPVIaq1qrH+ei2J+Q50Z/2RTAnQDL4DO3H7VgBqdBIGzMmwp6NeyczgyYAvW4CvrKfwfFPvH9oMz97krP8WG/vXA7Xd8YKZ3p9o/WcKxPtU5wymHbUffuAPG/EbyfKzHsCBLu1SLO75SRf+X5SW/Hbwt6xav4pavWbAt4BnLd+leo4ArSw/mwE4q3fjAlnhVKduXXkxnczh4r6Waaqn4nR3W6FsrP+JG1zv/wO26LOadDIn48UDfNIL8vD+n5IrBknbl5RqxL0RaJ153rpgme4Ui3S//XKqusqClxdQC2uEUZiA32D5LtWzGsCBn638OdAVKq0AZtfrAZRW1KjhezkoFBtdvwsHst4IelIIz5vYP7Ae8dxt7l1/Z9O+Dbur9TekgX+E9X9QIN6nDn4LU994iGnixCx7Irxtp3vJY9X0fNPx7gsuInrpCe574lamrpzKsfsdazVZWuKVOh3Ycd3BzqoT8WctPVZx4vLtxEuUVnjCaJe6rKNQeIVu017mXL9T/TIcwYQC4zE6uuG+77mSrxvqXcNO7vHbGR7gIi9XgvN78ZvSvqwVm6lU1os2PW+aO+3CR9rNvxseEjre849IHXPLllt4bs1zqeVnKnoO/EilISABvgX4jnDuvkAQeAGVqGJe0z6jsa6vZWOsT1yGTK2/3AEbVsOye5z132HTvlfZBW1eo0aASm/PZUJ4p6njPsGU1+1tCOCmcGV2B66SEiXl8GPDMgALvJ3l6zp/g0MOovtdV1LVVW7Y+Cv6N/cnvX2RjBL379w+0AB8dvQvm/ZlvYAQgryfZ+3QWvP8Pm+EsNYo/KJKa/Cd9bd1wpNJ7P9vm/at3d2t/48iQKW350Tgcq/USe6cD+HnfBAimUXbHO9HVv6ZNfiae/91ujafsiRoe88HaTv5Aip6iOvXXs+GyoYE6CQMWIFn0'
    'vU0rRs2u4jU+pMY6AXk/TyPiEfM8f1PTF1/g/CT6e5Uv7P+gfXO+jfZvP9lRnlS567wABf5fh71tu/RsU83wksXVJSxSvakozdu6vDN9vA7kFuQQEYy04Rp3rPjoq9ReuP72Kg3cv3a69lU3YQv/AZNIK2rdgo/Sffs2H9z/Hfgl3NlVm9ZTUQE04+EfFsG/CYSNMd+P2fz/sT6F1rwx4T1bzcBKr093xRCXKCO+iu6zjwlWU1TxpmO2QxoDYDGw1u9HcjStV7FmTl4zaSwHb9tF11B4Zj/xUa9kWvXXcvaLWsJ/CARcYkIbBX3m+I/gCc8Cn6BvJfn7vrdRg8ccl4a8x3waoTsTfjQ1g2VIcQLd7nY/3sb+zeOBevfriyg0ttzsYAvirapiFkXmZNty6PCE8Pn6m+D824Sp/BEsgJHkgVkVnRsXncPDaW/+SZcLdiy6EZuHPg150XnckDXAYm1N1QhM6A7q3chwBMexaBIZ6GTFQMrTP6/73Gwd0+LtK+V9dsRv3I7PPqfaCld3v/SWLL+bRKg0tvz18D3vWI76t0/on1GlxV4wtTPhSHAsH6CFktzOnE3Yorolu7VWa3VsHYLWmkKF3wNftlJdf5PuKVyC6dXT+eQSYdQzpUTt66VTqp6Uks84aG0IvCMxygFJdpybazavIr71H3G+o/+q1T4aTly2gfgF6DcaV77zE3Zmv+Ysv6tEqDS2/Nx4Go/V0K99QpKrzssnX0jNZ4vzHX+RAsv4B7q4ZY/4pDlsMUfWo8na6UJ3vM5ivseSzzvP7i//37mvfowb86dBUBbvg2hBKEy1UEpzPi/h0fgBxR8U+9fMbCC+9R9hsjHXACl7sbYr+JG60+WcsvZhg874mfGIOZlBnyGxor1j0iASm/PN4EvekEedfolFE46HRVLPOWZGb2eQEuvIQS4W610w/0WGDeAnSVP80IPmTLdcC98wpnkjzuD8MZvUV90HXdGdwKwaMMi9i/uz6TiJAr5Ap6tToUypC7rrBhYwUP6ISIiY/lvvBAOPMWO/7sh3ybrV+lyLngBFDvMTJ/GEb9+a/31sWL9wwhQ6e35c4T4P8B7hRDok/6e/Jnno8LYpHyeQig76hek670KIYY1fm6tKzhZLrWVE1Db10XsboN3/SP+eRcjf/8D4sev4XG9iL5aH6Jmhnc9PFTmz2UGzDwVccInzBu6GbzZAZ4k/Wsavc0VTer35F2OKI9geirHVOxPnLUDSwSFWTqu/z45kG+DKQfDzLfCoafh738Ani38CJFe/De7/JvwGyeCtFyluykUNJDB2/rFBPQIIcF9aPi14/HP/Rbesrl4rzyGrG4glmZOfj7fjS53E888Cw57s5mp6zp8XEu3s/64Phx8z4OgAOVumLY//Pwv0WZFryswizs8Dawrz+7bKYM+O6ojKPEAuXO+dk9015fP1zK8EK3/QodDiP4nYfVixCP/hgoKyEkz4bB3wevPpLDvdHuOZAY8tj0foJkAUg0XkDBiP5lW2/jRRx6PPOoMYrc+n1QQ1oncvP3sVO7sSF9S7ImHW3029St2wtJHXLfPEsw6fuvGovU3ECC8/QsKcx29hcBlwFEajkPro7WWBxNW9hFrnimy9lm8eVcStk1FHzQLjnsPhZn7JUDqZsts8vFbHQQa6WJALVyKW75tGL9iCUI1LtfSvEhTsnxLU0//SEUfl/rl26CjC+7+WXZFr35b9auNpdg/kgiUQB1T0nzKpjUPAJ1Ap4YD0foYKePD2bx6f/HENYjF11HPleHkzyGOn0WuvZCunK2GA93qAgm0IE0iDlullEqPrCdiCWQaOrPgJ7N44uHgK2lcf9b6nWcQvhF/5Q7oXwYblmNV/6OZ2B8zBrdmAijMRY6k/VFrgQJQBMpAH+YCi93Afhp9vJbxMcjNh4j7vwJzvkm4/0lw2qfJHXxQYs3JatnNwLUIDc3nPgkvLcJHct3AbFyIYxB2bb7sOj3ZDh/X1Jn9EDkC+C7+59tM6jfv310cmmcNZAO7cHbvDiOA/QFu8c56pbdH2FKxb1+XayLDc5iO18nAgVrrt+q4frx48YEusWIu0bTD4MTPkDvmBJROr7jhLDZLAKFbxFypzNRqR0tACw+hVVJmIFaI5ngdR6Y3L1mOtamn38V9J/rACD+1lfDt+abjpzIEL813gz4PWgMZZDfs9XvNhaAmQoRWeQpLiLwlQwlzefgXMK3P0zWcqpU8izXPHiFu+xTR3APgxM8QHPcmVBQnK201XCrF81oLLxmT7TIRrRShlI3qsHmFrmbwmzt5neofyfqFD7myqfs/fqP7vAU29m/ATPDU444AWyFFDMSV3p6qZf9Gawn9QBdmwaO7gNO0Vufw6vKjxJ2fQ87fH33ip/HfeIadeg0Cd9WMDJDDQM4YV3PLUfOa+04DiHqjwnfgZydzuLjfrPqbmz49z1h/Pg9P/9oVfv6A6fbZ7fr8R5UAWyF'
    'DzWoGR4ZX7MDI/cAZWutZeuPKo8Rdn0f+oQRv6sU//q0oIYybD8MUULWVtnkdb50IySjeVsBPhJ8crvqbwRe+yf2LnfD8Alf46bOFnw3sonV9dgsCtCJDpbdHYiY9DjaR4T7jEfR5hJU3iHu/jJp7BbypF+/Ys8wZjOxMnJH0QLNXsP0Aw0DTGfCz8/cbwHfkqA9v/UpHosC3qV97Byy+JjvNaw27weIOuw0BmnVDpbdHWd0wZN3kOkx79FwbGs6lNniMuOcS1HOnwMmfhH0ObIz9ciRgVJqwyBZkiSNwbeoybuzukVHG8uPUxWenemU7foKccf8b18KGZdjf0Ifp8x9Tgz47hQBNRNA2m4isUHJE6LcFlLO1VrPEirlHipfmo4/5OJz4Xii3meXXCNPcPesFfG84ORrSwAi0lx7PKv4s+K1q/c2ZQK5scv+Hr3bHHrbWP+YGfUZMcEb7A8qz+1R5dl8dsyLGapsxLAauBT6v4VdKxvDYj+En74Qn7oW2drOwUq5gLbQZYJm6+OSSa3EKaNLQ2QL8YbpCjlz2DYrGC6Tdvg9kyr4R42ALdtYH2UmRziNUrUfYAPwrcKvW+uOElbPE/V+F1Qvh+I9A99T0DaLYzNLNholWocFZPbQGP2v9rVx/cmZyxvqXzHGftSBT9q2O5dRvlxBgK0QYtCd1FfBOrdX54tlbj+D5u+Gkz6BPeAdiaBDUkHHt2VU4W1mxVCBGsOqtDfMOK/y0m8rfkhuzdf811pOF48H975QQsA0ihFZNv4wZWfsF8DkNd+m4Bg/9M+LOb5vFFTu6zVq7ze67+SocDU2dzdY/AvjN1u/njPrfsgmxcSU2m3kyk/pJxsnm7coPL8/u0/aSKFV7cpdjBqEuB76htXqKZ34L138Inpljll0ptqcXhMyCnngB2Rp8N8bf7DValYCDArR3wTN3uIbPxy0JBsaL+NstCNBEhMiKqzWYiyZdB/yDRt+twwriwa/DvP9vsoS2TrP8qu81WnxS4VPDXX9WK+gRJnsomQ77FkrZad4PWIKO2VG/3ZoAzfrAplmrMNfRuRT4oZIxLPo53H4ZrO+HzslmRq7wh6/Rp+T2uX4X77Ov8XOm4/flpa7pY6mt/G0cT+JvtyRAxhvENtautWnjVcBHtVZzWTEX7vgMLJ1vdEG5w4z+uda05gEfFQ/PEhpIkXmtZwd+iu3wzG9cfeFRm/qNK/G32xJgBG+w0rrhSzTcpqOqCQmLbjWeoNzRujTc3Nrdqtybfc7PG/cfBLDqYWfq82yWUhlP4m+XpYF/QkUxrvT2uNhbtQJxtZLx34gFP4TaRjjhAykBWgHfKu47Qrj/C/Im9y+1wbLH3MDPItK6f228Wf9u7QFaeINspvAdoFdr9QSLr4eHfpwWiXJl077lxGB2XR/VNPonfFvzz6fj/sV2eO6/mt3/mG76GPMEyHiDyKZiLwE3AJdprR/g2dvg5gvNC7umGjeeL6UgN4s+LwO85zcKQIA1Tzn3v9CGoApjfNh3zBOghUDstwB9SaPvJhwyL1q9FCbtlZLA81ISZMF3wNu1hfA8o/5X9jn373L/wfEo/sYkATJEcMWj9Zjr7V2i4TYA5v4zvDA/JYHnDxd+DnjVQv0vv9u5/z4r/sZd7j/mCZAJCXUL0nKgFzBX5Zj/HVi2ALqmmZp+kiLK1qHALfDse7Dqkaz632SJpiYIMDZ0AcD1Og4RD38bXnwUumdAqWu4FsgSwvX9rX7Ruf8lGfE3bt3/mCdANlW0hRoww8u/UHFoPcHD0DHdkMDPDxeEYPv+2mDVPDcJZYkVf0Pj2f2PCwK4Ek+mSNMPfAP4hY5DeOTfoP9p6JxmRWGLrMDPm9r/qvtc7f9RS6jaeHb/44kAjgTYlK0fmA1co+MQ5l4Bm1ZD995GE2Q31/kztBkxuA4rLF/YE9z/eCOA26QlwWrg68CviWpwby+EVWibYgaRkjPgmerf6iVm4Uozr2GTfY+Icb554/R3ORKsAf5Jw62EFbOYY3sXlCaneiCwl3RdcW82/RsgnSM5QYAxXCtwnuCLGu7khXvM9K6pe5uLOuWKafxf0+diyBM29x/37n9cEyDjCVzV8EqtNSy+AZ68I00P7aRPUd+CrSn02/8J2QO2cU2AzATXLda1f1FrBY9fDeuWQ/sUM+1r/TIX/1+y6r863tO/PcUDZOsEg5hr9/2UOITF15lQ0D0Z1ix2+f9yS5b6eE//9hgCZEjgOpC/quE2XnkCHroOr7MDVj/q8v9nrPXvEfF/jyFAhgRu7OD/aa1g0U9R/S/D+ufdy5bsSe5/jyKAJYFrLJkLXK2VhAe/izZjAptIZ/1MEGCcZwZbgK8AS/WLD7jn3WJP4Z6Q/++xBMjogQHMBFW3rbd1g93mur4TBBhdElSBH4lc8Tv26cesB5B7igDcYwmQDQVaRlfZx9faGkC8J50EkV3YeRxsGrOG4cB2vt4H2jALY'
    'QpMBXDIZgtj78f/CWsF7+kEcMve5aw3jK1niCcIsGcQwJHA7Tqz7zkEmNj23O1/BgBdHk5BlZEGtwAAAABJRU5ErkJggg==')

    data = base64.b64decode(data64)
    stream = StringIO(data)
    return wx.ImageFromStream(stream)

def get_cpa_bitmap(size=None):
    """The CellProfiler icon as a wx.Bitmap"""
    img = get_cpa_image()
    if size is not None:
        img.Rescale(size, size, wx.IMAGE_QUALITY_HIGH)
    return wx.BitmapFromImage(img)
    
def get_cpa_icon(size=None):
    """The CellProfiler icon as a wx.Icon"""
    icon = wx.EmptyIcon()
    if size == None and sys.platform.startswith('win'):
        size = 32
    icon.CopyFromBitmap(get_cpa_bitmap(size))
    return icon
    
