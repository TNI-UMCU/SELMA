# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 11:53:44 2020

@author: user
"""
#%%

import numpy as np
import cv2
import matplotlib.pyplot as plt
import pydicom

#%%

path = r'C:/Users/spham2.DS/Documents/SELMA/Resolution Data/RESOLUTION-C006_7_MRI_HERSENEN_20200228/1001/DICOM/1.2.826.0.1.3680043.9.6827.2264656684580682758133681284734286788-1001-1-1dw3chw.dcm'
im = pydicom.dcmread(path).pixel_array

#%%

im2     = np.asarray(im > np.percentile(im, 40), dtype='uint8')
kernel  = np.ones((15,15), dtype='uint8')
im3     = cv2.erode(im2[0,:,:], kernel)
plt.imshow(im3)

kernel2  = np.ones((50,50), dtype='uint8')
im4     = cv2.dilate(im3, kernel2, 1)
plt.imshow(im4)


#fill hole

im5     = np.copy(im4)
h,w     = im5.shape
mask    = np.zeros((h+2, w+2), np.uint8)

cv2.floodFill(im5, mask, (0,0), 1)
cv2.floodFill(im5, mask, (h-1,w-1), 1)
plt.imshow(im5)

im6     = cv2.bitwise_not(im5)
im6     = im6 == np.max(im6)
plt.imshow(im6)

im7     = im4 | im6
plt.imshow(im7)

kernel3     = np.ones((80,80), dtype='uint8')
im8     = cv2.erode(im7, kernel3, 1)
plt.imshow(im8)

plt.imshow(im[0,:,:]*im8)
