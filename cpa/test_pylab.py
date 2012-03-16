


import PIL.Image as Image
import pylab
import numpy as np


pylab.figure()

#im = Image.open("/Users/afraser/Pizzabarn.jpg")
#ivals = np.array(im.getdata())
#ivals = ivals.reshape((im.size[1], im.size[0], 3))
#pylab.imshow(ivals[:,:,1], cmap=pylab.cm.gray, aspect='auto')
#pylab.axis('tight')
#pylab.axis('off')
#pylab.subplots_adjust(0.,0.,1.,1.)

a = np.ones(1000)
a = a.reshape((100,10))
pylab.imshow(a)

pylab.show()
