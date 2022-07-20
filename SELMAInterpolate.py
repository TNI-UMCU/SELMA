#!/usr/bin/env python

"""
This static module contains the following functions:

+ :function:`getLibraries`    
+ :function:`getTransMatrix`
+ :function:`doInterpolation`

"""

import numpy as np
import pydicom
from PyQt5 import (QtCore, QtGui, QtWidgets)
from scipy.interpolate import RegularGridInterpolator

def getLibraries(self):
    """
        Checks for the existence of necessary libraries, prompts the user if
        none exist. 
        
        returns: 
            A list with all the libraries
    """

    COMPANY = "UMCu"
    APPNAME = "SELMA"

    settings = QtCore.QSettings(COMPANY, APPNAME)
    
    libs    = []
 
    #SPM
    try:
        dirname     = settings.value("spmDir")
        
        if dirname is None:
                                
            dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                      caption =
                                                      'Open SPM12 folder')
            settings.setValue("spmDir",      dirname)
            
    except:
        
        dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                      caption =
                                                      'Open SPM12 folder')
        settings.setValue("spmDir",      dirname)
        
    libs.append(dirname)
        
    try:
        dirname     = settings.value("dcm2niiDir")
        
        if dirname is None:
            
            dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                      caption =
                                                      'Open dcm2nii folder'
                                                      )
        
            settings.setValue("dcm2niiDir",      dirname)
            
    except:
        
        dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                      caption =
                                                      'Open dcm2nii folder'
                                                      )
        
        settings.setValue("dcm2niiDir",      dirname)
    
    libs.append(dirname)
    
    return libs

def getTransMatrix(info):
    '''Returns the rotation and transformation matrices based on the image 
    position and image orientation for a dicom info object.'''
    
    # import pdb; pdb.set_trace()
    #Find the rightmost(?) frame and get the ImagePositionPatient from there
    maxIdx  = 0
    maxVal  = -1e10
    vals = []
    
    if type(info) is list:
        
        i = 0
        
        for frame in info:
            
            T1dcm = pydicom.dcmread(frame)
            val     = T1dcm.ImagePositionPatient[0]
            vals.append(val)
            
            if float(val) > maxVal:
                maxVal = float(val)
                maxIdx   = i
                
            i = i + 1
        
        info = pydicom.dcmread(info[maxIdx])
            
        ipp = info.ImagePositionPatient
        ipp = [float(ipp[0]), float(ipp[1]), float(ipp[2])] #coordinates of right most pixel
        iop = info.ImageOrientationPatient # orientation (direction of axes)
        ps  = info.PixelSpacing 
        ps  = [float(ps[0]), float(ps[1])] # Pixel spacing
        st  = float(info.SliceThickness) #Slice thickness
        
    else:
    
        for i in range(info.pixel_array.shape[0]):
            val     = info.PerFrameFunctionalGroupsSequence[i].\
                                      PlanePositionSequence[0].\
                                      ImagePositionPatient[0]
                                       
            if float(val) > maxVal:
                maxVal = float(val)
                maxIdx   = i
           
        ipp = info.PerFrameFunctionalGroupsSequence[maxIdx].\
                    PlanePositionSequence[0].\
                    ImagePositionPatient
        ipp = [float(ipp[0]), float(ipp[1]), float(ipp[2])] #coordinates of right most pixel
        iop = info.PerFrameFunctionalGroupsSequence[0].\
                    PlaneOrientationSequence[0].\
                    ImageOrientationPatient # orientation (direction of axes)
        ps  = info.PerFrameFunctionalGroupsSequence[0].\
            PixelMeasuresSequence[0].\
                PixelSpacing 
        ps  = [float(ps[0]), float(ps[1])] # Pixel spacing
        st  = float(info.
                  PerFrameFunctionalGroupsSequence[0]
                  [0x2005,0x140f][0].SliceThickness) #Slice thickness


    #%Translate to put top left pixel at ImagePositionPatient
    Tipp = [[1, 0, 0, ipp[0]],
            [0, 1, 0, ipp[1]],
            [0, 0, 1, ipp[2]],
            [0, 0, 0, 1] ]
    
    #Rotate into patient coordinate system using direction 
    #cosines from ImagOrientationPatient
    r   = [float(iop[0]), float(iop[1]), float(iop[2])]
    c   = [float(iop[3]), float(iop[4]), float(iop[5])]
    s   = np.cross(r,c)    
    R   = [[r[0], c[0], s[0], 0],
           [r[1], c[1], s[1], 0],
           [r[2], c[2], s[2], 0],
           [0,  0,  0,  1]]
    
    #Scale using PixelSpacing
    if info.MRAcquisitionType != '2D':
        try:
                st = float(info.SpacingBetweenSlices)
        except:
            if 'philips' in info.Manufacturer.lower():
                dcmFrameAddress             = 0x5200, 0x9230
                dcmPrivateCreatorAddress    = 0x2005, 0x140f
                page    =   info[dcmFrameAddress][0]            \
                            [dcmPrivateCreatorAddress][0]       
                st      =   float(page.SpacingBetweenSlices)
    S = [  [ps[1], 0, 0, 0],
           [0, ps[0], 0, 0],
           [0, 0, st, 0],
           [0, 0, 0, 1]]
           
    
    #Shift image to make top left voxel centre at (0,0,0)
    T0 = [  [1, 0, 0, 0],
           [0, 1, 0, 0],
           [0, 0, 1, 0],
           [0, 0, 0, 1]]
    
    #Construct transformation matrix
    M = np.dot(
            np.dot(
                np.dot(Tipp, R), S), T0)
    
    return M, R

def doInterpolation(M, t1im, pcaShape):
        '''
        Interpolates the 3d t1 image at the locations of the pca grid defined
        by the transformation matrix M.
        
        Note: most of this code is converted from the matlab PulsateGUI 
        program. It has been tested and seems to work, but many of the steps
        are only empirically verified (= I don't know why everything works
                                       the way it does.)
        
        '''

        #swap axes for x and y 
        t1toqfnew = np.zeros((4,4))
        t1toqfnew[:,0] = M[:,1]
        t1toqfnew[:,1] = M[:,0]
        t1toqfnew[:,2] = M[:,2]
        t1toqfnew[:,3] = M[:,3]
        
        #Switch axes to x,y,z so that it is the same as matlab
        #There's probably a way to combine the next few steps into one, 
        #but this works
        t1  = t1im
        t1  = np.flip(t1, 1)
        t1  = np.swapaxes(t1, 0,2)
        
        #Reorient the image such that it maches the LPH orientation of the PCA
        t1_3D = np.flip(t1,1)
        t1_3D = np.flip(t1_3D,2)
        t1_3D = np.swapaxes(t1_3D, 1,0)
        
        # get coordinate ranges
        corrcoorx = -0.5
        corrcoory = -1.5
        corrcoorz = -1.5
        Zrange = 1
        
        range_x = np.arange(1, pcaShape[2] + 1) + corrcoorx
        range_y = np.arange(1, pcaShape[1] + 1) + corrcoory
        range_z = Zrange + corrcoorz;
        
        #Finalise transformation matrix
        M = t1toqfnew + [[0,0,0,1],[0,0,0,1],[0,0,0,1],[0,0,0,0]]
        
        #Shift coordinates (this probably isn't necessary in python, but I 
        # haven't verified that.)
        dV =  [-0.5, -0.5, -0.5]        
        range_x = range_x - dV[0]
        range_y = range_y - dV[1]
        range_z = range_z - dV[2]
        yg, xg, zg = np.meshgrid(range_y,range_x,range_z)
        
        xyz = np.asarray([
               np.reshape(xg,-1),
               np.reshape(yg,-1),
               np.reshape(zg, -1),
               np.ones(len(xg)**2)])
        
        #Construct interpolation coordinates
        uvw = np.dot(M, xyz)
        uvw = np.transpose(uvw[:3,:])
        
        # interpolate
        #Here we vary from lennart's method, as we have to use 
        #scipy.RegularGridInterpolator
        
        #Get interpolation coordinates
        xi = uvw[:,0]
        yi = uvw[:,1]
        zi = uvw[:,2]
        
        #Find only values that lie within the t1 space
        index = (xi > 0) * (xi < t1_3D.shape[0] - 1) * \
                (yi > 0) * (yi < t1_3D.shape[1] - 1) * \
                (zi > 0) * (zi < t1_3D.shape[2] - 1)
        xi = xi[index]
        yi = yi[index]
        zi = zi[index]
        
        # For some reason, we have to switch x and y. I really don't 
        # understand why. 
        pts = np.transpose((yi, xi, zi))   
        
        #### Create interpolation space
        x = np.arange(0,t1_3D.shape[0])
        y = np.arange(0,t1_3D.shape[1])
        z = np.arange(0,t1_3D.shape[2])
        inter = RegularGridInterpolator((x,y,z), t1_3D)
   
        # Interpolate at the pca coordinate locations
        inp     = inter(pts)
        
        #Insert the interpolated values in a new slice
        res = np.zeros(len(index))
        res[index] = inp
        res = np.reshape(res, xg.shape[:2])
        
        #### Experimental: flip on column axis
        res     = np.flip(res, 1)
        
        #Store the interpolation result
        return res





##### Old stuff Can probably be removed.
# def usableImagePosition(dcm):
#     pos     = dcm[0x5200, 0x9230][0][0x0020, 0x9113][0].ImagePositionPatient
#     return np.array([float(pos[0]), float(pos[1]), float(pos[2])])

# def usableImageOrientation(orr):
#     xx, xy, xz, yx, yy, yz = orr
#     row   = np.asarray([float(xx), float(xy), float(xz)])
#     col   = np.asarray([float(yx), float(yy), float(yz)])
    
#     return row, col

# def rotXAxis(r, theta = math.pi/2 ):
#     '''
#     Rotates a 3x1 vector around the x-axis for 90 degrees
#     '''
    
#     rotMat  = np.asarray([[1, 0, 0],
#                           [0, 0, -1],
#                           [0, 1, 0]])
    
#     return  np.dot(rotMat, r)


# def rotYAxis(r):
#     '''
#     Rotates a 3x1 vector around the y-axis for 90 degrees
#     '''
    
#     rotMat  = np.asarray([[0, 0, 1],
#                           [0, 1, 0],
#                           [-1,0, 0]])
    
#     return  np.dot(rotMat, r)

# def rotZAxis(r):
#     '''
#     Rotates a 3x1 vector around the z-axis for 90 degrees
#     '''
    
#     rotMat  = np.asarray([[0, -1,0],
#                           [1, 0, 0],
#                           [0, 0, 1]])
    
#     return  np.dot(rotMat, r)


# def findAngleDiff(orr1, orr2):
#     '''
#     Finds the difference in radians between two directional cosine vectors 
#     along each axis.
#     Subtracts pi/2 to get the angle from zero.
#     '''
    
#     dTheta  = math.acos(orr1[0] - orr2[0]) - math.acos(0)
#     dPhi    = math.acos(orr1[1] - orr2[1]) - math.acos(0)
#     dKsi    = math.acos(orr1[2] - orr2[2]) - math.acos(0)
    
#     return np.array([dTheta, dPhi, dKsi])



# def getInterpolationVariables(dcm, rescaledImage = None):
#     """
#     Constructs a list of the real-world-coordinates of dicom file, as well
#     as a list of the values. 
#     The function is invariant to the orientation of the image.
    
#     Input:
#         dcm             -   dicom header; the output from pydicom.dcmread
#         rescaledImage (optional) - the rescaled Dicom image array. 
        
#     Returns:
#         x   - list of all the real-world x-coordinates
#         y   - list of all the real-world y-coordinates
#         z   - list of all the real-world z-coordinates
#         vals- list containing the rescaled values at each rwc. (only if 
#         rescaledImage is provided).
#     """
    
    
#     #First get the necessary variables
#     pixelSpacing = dcm[0x5200, 0x9230][0][0x0028, 0x9110][0][0x0028, 0x0030].value
#     if rescaledImage is not None:
#         shape   = rescaledImage.shape
#     else:
#         shape        = dcm.pixel_array.shape
#     row_orr, col_orr    = usableImageOrientation(
#             dcm[0x5200, 0x9230][0][0x0020, 0x9116][0].ImageOrientationPatient)
    
#     # Preallocate Output variables
#     x       = np.zeros(shape[0]*shape[1]*shape[2])
#     y       = np.zeros(shape[0]*shape[1]*shape[2])
#     z       = np.zeros(shape[0]*shape[1]*shape[2])
#     vals    = np.zeros(shape[0]*shape[1]*shape[2])

#     #Iterate over slices
#     for i in range(shape[0]):
#         #Find top left voxel position of that slice
#         r0  = dcm[0x5200, 0x9230][i][0x0020, 0x9113][0].ImagePositionPatient
        
#         #Find rwc for all three coordinate directions of every voxel in the 
#         #slice. This is done by taking the position of the top left voxel of 
#         #this slice (r0) and propagating in the row and column directions of
#         #the slice. The directional cosines (row_orr, col_orr) are used to
#         #determine how the rows and columns are oriented with respect to 
#         #all three coordinate axes.
        
#         #A 2d matrix is made for each coordinate axis showing the position
#         #of each voxel in the current slice relative to the top left voxel.
#         #The top left voxel position is then added to find the real world
#         #coordinate of every voxel.
        
#         #These coordinates are then added to the output lists for the x,y and z
#         #axes.
        
#         #first coordinate axis
#         c01 = np.ones([shape[1], shape[2]]) * (np.arange(0,shape[1]) * 
#                                                     pixelSpacing[0] * 
#                                                     row_orr[0])
#         c02 = (np.arange(0,shape[2]) * 
#               pixelSpacing[1] * 
#               col_orr[0])    * np.ones([shape[1], shape[2]])
#         c02 = np.transpose(c02)
        
#         c0  = r0[0] + c01 + c02
        
#         #second coordinate
#         c11 = np.ones([shape[1], shape[2]]) * (np.arange(0,shape[1]) * 
#                                                     pixelSpacing[0] * 
#                                                     row_orr[1])
#         c12 = (np.arange(0,shape[2]) * 
#               pixelSpacing[1] * 
#               col_orr[1])    * np.ones([shape[1], shape[2]])
#         c12 = np.transpose(c12)
        
#         c1  = r0[1] + c11 + c12
        
#         #third coordinate
#         c21 = np.ones([shape[1], shape[2]]) * (np.arange(0,shape[1]) * 
#                                                     pixelSpacing[0] * 
#                                                     row_orr[2])
#         c22 = (np.arange(0,shape[2]) * 
#               pixelSpacing[1] * 
#               col_orr[2])    * np.ones([shape[1], shape[2]])
#         c22 = np.transpose(c22)
        
#         c2  = r0[2] + c21 + c22
        
#         #Create x,y,z lists for this slice
#         points    = np.array([c0,c1,c2])
#         #Reshape coordinates to list
#         [xslice, yslice, zslice]  = np.reshape(points, (3, -1))
#         # [zslice, yslice, xslice]  = np.reshape(points, (3, -1))
        
#         #Create value list for this slice        
#         if rescaledImage is not None:
#             imSlice     = rescaledImage[i]
#             valSlice    = np.reshape(imSlice, -1)
#         else:
#             valSlice    = []
        
#         #Add to output
#         x[i * shape[1]*shape[2] : (i+1)*shape[1]*shape[2]] = xslice
#         y[i * shape[1]*shape[2] : (i+1)*shape[1]*shape[2]] = yslice
#         z[i * shape[1]*shape[2] : (i+1)*shape[1]*shape[2]] = zslice
#         vals[i * shape[1]*shape[2] : (i+1)*shape[1]*shape[2]] = valSlice
        
#     return x, y, z, vals
    
    