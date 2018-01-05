
import numpy as np
import scipy
from scipy.misc import imread, imsave
from scipy.ndimage.morphology import distance_transform_edt as d

clean = imread('./clean.png')
clean[clean==0] = 1
clean[clean==255] = 0

proximity = d(clean)
print(np.unique(proximity))
# imsave('proximity.png', proximity)
