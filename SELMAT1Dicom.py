#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SELMAT1Dicom`

"""

# ====================================================================

import SELMADicom
import SELMAInterpolate

import pydicom
import SimpleITK as sitk
import numpy as np
#import matlab.engine


class SELMAT1Dicom(SELMADicom.SELMADicom):
    """
    This class deals with t1 segmentation
    """

    def __init__(self, dcmFilename, pcaDcm):
        """
        Load & rescale the T1 & interpolate correct slice
        """
        self._dcmFilename = dcmFilename
        self._dcm = pydicom.dcmread(self._dcmFilename)
        self._pcaDcm = pcaDcm

        #############################################################
        # Declare some variables for use in interpolating / segmenting

        # T1 properties
        self._manufacturer  = None
        self._frames        = None
        self._numFrames     = None
        self._t1Slice       = None
        self._magFrameIndex = None

        # interpolating properties
        self._M             = None
            #transformation matrix between this T1 & pca

        # Segmentation properties
        self._maskSlice     = None
        self._segmentation  = None

        #############################################################

        # Get only the magnitude frames from the T1
        self.findManufacturer()
        self.findMagnitudeFrames()

        # Interpolate the t1 slice
        self.orderFramesOnPosition()
        self.interpolateT1()

    '''Public'''

    def getSegmentationMask(self):
        """
        Walks through the various functions for constructing a T1 segmentation.
        
        -Find libraries (SPM & dcm2nii)
        -Launch matlab engine
        -Run matlab script to convert to .nii & segment
        -Remove unnecessary files
        -Interpolate segmentation slice from brainmask           
            
        Returns:
            self._segmentation; the interpolated slice of the brainmask
        """
        
        if self._maskSlice is None:
            self.segmentAndInterpolateMask()
        
        return self._maskSlice

    def getFrames(self):
        """
            Override of SELMADicom getFrames function. Only returns the 
            interpolated pca slice. 
        """

        return self._t1Slice

    '''Private'''

    def findManufacturer(self):
        """
            Finds the manufacturer in the dicom tags
        """
        self._manufacturer = self._dcm[0x8, 0x70].value

    def findMagnitudeFrames(self):
        """
            Finds the magnitude frames in the T1 dicom and stores the indices.        
        """

        self._magFrameIndex = []

        if 'philips' in self._manufacturer.lower():
            for i in range(len(self._dcm.pixel_array)):
                dcmFrameAddress = 0x5200, 0x9230
                dcmPrivateCreatorAddress = 0x2005, 0x140f
                dcmImageTypeAddress = 0x0008, 0x0008

                frameType = self._dcm[dcmFrameAddress][i] \
                    [dcmPrivateCreatorAddress][0] \
                    [dcmImageTypeAddress].value[2]
                if frameType == "M_FFE":
                    self._magFrameIndex.append(i)

                    # other manufacturers
                    
        else:
            self._magFrameIndex     = np.ones(self._dcm.pixel_array.shape[0])

        self._frames = self._dcm.pixel_array[self._magFrameIndex]
        self._numFrames = len(self._frames)

    ######################################################################
    # Functions dealing with the segmentation & interpolation of T1 & mask

    def orderFramesOnPosition(self):
        '''
        Looks at the order the frames are in and sorts them if they are not 
        continuously increasing to the left
        '''
        
        LRPos   = []
        for idx in self._magFrameIndex:
            pos     = self._dcm.PerFrameFunctionalGroupsSequence[idx].\
                                             PlanePositionSequence[0].\
                                              ImagePositionPatient[0]
            LRPos.append(float(pos))                                              
            
        order           = np.argsort(LRPos)
        order           = order[::-1]
        orderedFrames   = self._frames[order,:,:]
        
        self._frames    = orderedFrames
        
    
    def interpolateT1(self):
        '''
        Interpolates a slice in the T1 image to match with the pca slice.
        '''
        
        #First, construct the 
        Mpca, Rpca  = SELMAInterpolate.getTransMatrix(self._pcaDcm)
        Mt1, Rt1    = SELMAInterpolate.getTransMatrix(self._dcm)
        self._M     = np.dot(np.linalg.inv(Mt1), Mpca)
        pcaShape    = self._pcaDcm.pixel_array.shape
        
        self._t1Slice   = SELMAInterpolate.doInterpolation(self._M,
                                                           self._frames,
                                                           pcaShape)
        
    def segmentAndInterpolateMask(self):
        '''
        Calls the matlab code that runs the SPM segmentation on the t1 dicom.
        Loads and interpolates the resulting WM mask.
        '''
  
        #Prepare for matlab call
        libraries = SELMAInterpolate.getLibraries(self)
        spm = libraries[0]
        dcm2nii = libraries[1]

        eng = matlab.engine.start_matlab()

        wm = eng.spmSegment(self._dcmFilename,
                             spm,
                             dcm2nii)

        # Load the WM segmentation
        im = sitk.ReadImage(wm)
        im = sitk.GetArrayFromImage(im)
        im = np.flip(im, 1)
        im = np.flip(im, 0)
        im = np.swapaxes(im,0,2)
        im = np.swapaxes(im,1,2)
        
        self._segmentation = im

        # Create interpolated slice
        pcaShape        = self._pcaDcm.pixel_array.shape
   
        self._maskSlice = SELMAInterpolate.doInterpolation(self._M,
                                                           self._segmentation,
                                                           pcaShape)


