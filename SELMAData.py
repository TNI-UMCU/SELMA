#!/usr/bin/env python

"""
This module is contains all the relevant classes that form the data layer 
of the SELMA project. It contains the following classes:

+ :class:`SELMADataObject`
    
"""

# ====================================================================
import numpy as np
from skimage import measure 
from scipy.ndimage import gaussian_filter
import scipy.signal
import scipy.stats
import cv2
import threading

#from multiprocessing import Pool, freeze_support, cpu_count

from PyQt5 import QtCore

# ====================================================================

import SELMADicom
import SELMAClassicDicom
import SELMAT1Dicom
import SELMADataIO
import SELMAGUISettings
import SELMADataClustering
import SELMADataCalculate
import SELMADataSelection

# ====================================================================

# -------------------------------------------------------------
'''Auxillary functions, used in the vessel analysis'''

def div0(a, b ):
    """ Divide function that ignores division by 0:
        div0( [-1, 0, 1], 0 ) -> [0, 0, 0] """
    #from: https://stackoverflow.com/questions/26248654/
    #   how-to-return-0-with-divide-by-zero
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide( a, b )
        c[ ~ np.isfinite( c )] = 0  # -inf inf NaN
    return c

def applyMedianFilter(obj):
    """Performs a median filter on the array with the specified diameter"""
    diameter, array = obj
    return scipy.signal.medfilt2d(array, diameter)


class SELMADataObject:
    """This class stores all data used in the program. It has a SELMADicom
    object for the Dicom image of the flow data, as well as the T1.
    Any segmentation and vessel masks are also stored here.
    
    The class furthermore contains all the methods for analysing and 
    directly handling the data. It is called by SELMADataModels, which 
    manages the user specified settings."""
    
    def __init__(self,
                 signalObject,
                 dcmFilename = None,
                 classic = False):
        
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        self.settings = QtCore.QSettings(COMPANY, APPNAME)
        
        self._mask          = None
        self._NBmask        = None      #Non binary mask, no treshold applied
        self._t1            = None
        self._vesselMask    = None
        self._selmaDicom    = None
        
        if dcmFilename is not None:
            if classic:
                self._selmaDicom    = SELMAClassicDicom.SELMAClassicDicom(
                                                            dcmFilename)
                self._dcmFilename   = dcmFilename[0] + ".dcm"
            else:
                self._selmaDicom    = SELMADicom.SELMADicom(dcmFilename)
                self._dcmFilename   = dcmFilename 
            
        self._signalObject = signalObject
    
    '''Public'''
    
    # 
    # ------------------------------------------------------------------
    
    def analyseVessels(self, BatchAnalysisFlag):
        '''
        The main algorithm of segmenting & analysing the significant vessels.
        It is split in the following parts:
            -Preprocesses the data to be a gaussian around zero.
            -Find all significant voxels based on their SNR
            -Cluster results into vessels
            -Extract and save vessel properties
        '''
        if self._selmaDicom is None:
            self._signalObject.errorMessageSignal.emit("No DICOM loaded.")
            return
        
        if (self._readFromSettings('BasalGanglia') + 
            self._readFromSettings('SemiovalCentre') + self._readFromSettings('MiddleCerebralArtery')
            ) == 0:
            
            self._signalObject.errorMessageSignal.emit("No structure " +
            "selected. Please select a structure from the structure list in "+ 
            "the bottom right hand corner.")
            
            return
 
        if self._readFromSettings('AdvancedClustering'):
            
            if (self._readFromSettings('PositiveFlow') + 
                self._readFromSettings('NegativeFlow') +
                self._readFromSettings('PositiveMagnitude') + 
                self._readFromSettings('NegativeMagnitude') +
                self._readFromSettings('IsointenseMagnitude')) == 0:
                
                self._signalObject.errorMessageSignal.emit("Invalid cluster " 
                + "selection. Please make a magnitude and flow cluster " +
                "selection in the Advanced Clustering tab in the settings.")
                return 
            
        if self._readFromSettings('manualSelection') and (BatchAnalysisFlag == False
        and self._readFromSettings('BasalGanglia')):
            
            self.settings.setValue('removeNonPerp',          'false')
            self.settings.setValue('deduplicate',            'false')
            
        if self._readFromSettings('MiddleCerebralArtery'):
    
            self.settings.setValue('removeNonPerp',          'false')
            self.settings.setValue('deduplicate',            'false')
        
        self._signalObject.setProgressBarSignal.emit(0)
        self._signalObject.setProgressLabelSignal.emit(
                    "Calculating median images")
        self._calculateMedians()
        self._signalObject.setProgressBarSignal.emit(60)
        self._signalObject.setProgressLabelSignal.emit(
                    "Finding significant vessels")
        self._subtractMedian()
        
        #Estimate STD of noise in mean Velocity
        #self._estimateVelocitySTD()
                
        #Determine SNR of all voxels
        self._SNR()
        
        #Find all vessels with significant flow.
        self._findSignificantFlow()

        #Adjust and apply the Mask
        self._removeZeroCrossings()
        self._removeGhosting()
        self._removeOuterBand()
        self._updateMask()
        self._applyT1Mask()
        self._signalObject.setProgressBarSignal.emit(80)
        self._signalObject.setProgressLabelSignal.emit(
                    "Analysing clusters")
        
        #Cluster the vessels. 
        self._findSignificantMagnitude()
        self._clusterVessels()
        self._removeNonPerpendicular()
        self._deduplicateVessels()
        self._createVesselMask()
        self._signalObject.setProgressBarSignal.emit(100)
        
        self._Included_Vessels = []
        self._Excluded_Vessels = []
        self.VesselCounter = 0
        
        #Send vessels back to the GUI for vessel selection
        self._signalObject.sendVesselMaskSignal.emit(self._vesselMask)
 
        if self._readFromSettings('manualSelection') and (BatchAnalysisFlag == False
        and self._readFromSettings('BasalGanglia')):
            
            self.settings.setValue('removeNonPerp',          'false')
            self.settings.setValue('deduplicate',            'false')
            self._manualSelection()
            
            if self._clusters == []:
                
                self._included_vessels = []
                self.stopSelection()
            #self._calculateParameters()
            
        else:
            
            self._calculateParameters()
                   
            #make dictionary and write to disk
            self._signalObject.setProgressLabelSignal.emit(
                        "Writing results to disk")
            self._makeVesselDict()
            
            SELMADataIO._writeToFile(self)
        
            self._signalObject.setProgressLabelSignal.emit("")
        
    def VesselSelected(self, state):
    
        if state == 0:
        
            self._Excluded_Vessels.append(self.VesselCounter)
            
        elif state == 1:
        
            self._Included_Vessels.append(self.VesselCounter)
            
        self.VesselCounter = self.VesselCounter + 1
        
        if self.VesselCounter < len(self._clusters):
  
            SELMADataSelection.SELMADataSelection.VesselSelection(self)
            
        else:
            
            SELMADataSelection.SELMADataSelection.FinishSelection(self)
            
    def repeatSelection(self, state):
        
        self._Excluded_Vessels = []
        self._Included_Vessels = []
        self.VesselCounter = state
        self._createVesselMask()
        
        SELMADataSelection.SELMADataSelection.VesselSelection(self)
        
    def stopSelection(self):

        self._clusters = self._included_vessels
        
        self._calculateParameters()
        
        #make dictionary and write to disk
        self._signalObject.setProgressLabelSignal.emit(
                        "Writing results to disk")
        self._makeVesselDict()
            
        SELMADataIO._writeToFile(self)
        
        self._signalObject.setProgressLabelSignal.emit("")
        
    def segmentMask(self):
        if self._t1 is None:
            self._signalObject.errorMessageSignal.emit(
                    "Please load a t1 dicom first.")
            return
        
        self._signalObject.setProgressLabelSignal.emit(
            "Segmenting white matter from T1 - This may take a while.")
  
        self._NBmask  = self._t1.getSegmentationMask()
        self._thresholdMask()
        self._signalObject.setProgressLabelSignal.emit(
                    "")
    
    #Getter functions
    # ------------------------------------------------------------------    
    def getFrames(self):
        return self._selmaDicom.getFrames()
    
    def getRawFrames(self):
        return self._selmaDicom.getRawFrames()
    
    def getNumFrames(self):
        return self._selmaDicom.getNumFrames()

    def getMask(self):
        if self._NBmask is None:
            return self._mask
        else:
            self._thresholdMask()
            return self._mask
    
    def getT1(self):
        return self._t1

    def getNoiseScalingFactors(self):
        return self._selmaDicom.getTags()['R-R Interval'], self._selmaDicom.getTags()['TFE'], self._selmaDicom.getTags()['TR'], self._selmaDicom.getTags()['Temporal resolution']

    def getVenc(self):
        return self._selmaDicom.getTags()['venc']
    
    def getRescale(self):
        velFrames   = self._selmaDicom.getVelocityFrames()
        minres      = np.min(velFrames)
        maxres      = np.max(velFrames)
        
        return [minres, maxres]
    
    def getVesselMask(self):
        return self._vesselMask
#    
    def getVesselDict(self):
        return self._vesselDict, self._velocityDict
    
    def getDcmFilename(self):
        return self._dcmFilename
    
    #Setter functions
    # ------------------------------------------------------------------    
    
    def setMask(self, mask):
        self._mask = mask
        
    def setT1(self, t1Fname):
        self._t1 = SELMAT1Dicom.SELMAT1Dicom(t1Fname, 
                                             self._selmaDicom.getDCM())
        
    def setVenc(self, venc):
        self._selmaDicom.setVenc(venc)
        
    def setVelRescale(self, rescale):
        self._selmaDicom.setVelRescale(rescale)
        
    '''Private'''
    # Setup data from .dcm file
    # ------------------------------------------------------------------    
    
    
    def _readFromSettings(self, key):
        """Loads the settings object associated with the program and 
        returns the value at the key."""
        
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        settings = QtCore.QSettings(COMPANY, APPNAME)
        val = None
        
        try:
            val = settings.value(key)
        except:
            self._signalObject.errorMessageSignal.emit(
                "Wrong setting accessed.")
            return val
        
        #Return the right type
        if val == "true":
            return True
        if val == "false":
            return False
        
        return float(val)
    
    
    def _getSigma(self):
        """ Returns the upper end of the confidence interval with the alpha
        value in the settings.
        
        Args:
            
        Returns:
            interval(float): upper end of confidence interval.
        """
               
        alpha       = self._readFromSettings('confidenceInter') #0.05
        alpha       = 1 - alpha
        
        interval    = scipy.stats.norm.interval(alpha)[1]

        return interval    
    
        
    def _thresholdMask(self):
        #threshold the mask based on the value in the settings
        threshold   = self._readFromSettings("whiteMatterProb")
        self._mask  = np.copy(self._NBmask)
        self._mask[self._mask < threshold]  = 0
        self._mask[self._mask >= threshold] = 1
        self._mask = np.asarray(self._mask, dtype=int)
    
        
    
    # ------------------------------------------------------------
    """Vessel Analysis"""
    
    def _getMedianDiameter(self):
        """Returns the diameter as specified in the settings."""
        
        diam    = self._readFromSettings("medDiam")
        if diam is None:
            diam    = 0
            
        mmPix   = self._readFromSettings("mmPixel")
        if mmPix:
            ps      = self._selmaDicom.getPixelSpacing()
            newDiam = int(diam / ps)
            if newDiam % 2 == 0:
                newDiam += 1
            diam    = newDiam
         
        return diam
    
    
    def _calculateMedians(self):
        """Applies median filters to some necessary arrays.
        Starts a new process for each, to reduce processing time."""

        #Prepares the data to be filtered
        diameter = int(self._getMedianDiameter())

        #phase Frames are used in the 3T Test Retest data
        velocityFrames  = np.asarray(self._selmaDicom.getVelocityFrames()) 
        magnitudeFrames = np.asarray(self._selmaDicom.getMagnitudeFrames())
        
        meanVelocityFrame       = np.mean(velocityFrames, axis=0)
        meanMagnitudeFrame      = np.mean(magnitudeFrames, axis=0)
  
        venc                = self._selmaDicom.getTags()['venc']
        phaseFrames         = velocityFrames * np.pi / venc
    
        complexSignal       = magnitudeFrames * (
                                                np.cos(phaseFrames) + 
                                                np.sin(phaseFrames) * 1j
                                                )

        realSignalSTD       = np.std(np.real(complexSignal), axis = 0, ddof=1)
        imagSignalSTD       = np.std(np.imag(complexSignal), axis = 0, ddof=1)
        
        rmsSTD              = np.sqrt( (realSignalSTD**2 + imagSignalSTD**2))
        
        #Multithreaded version, not very stable.
#        objList = [(diameter, meanVelocityFrame),
#                   (diameter, meanMagnitudeFrame),
#                   (diameter, rmsSTD)]
#        
#        nProcesses = min(cpu_count(), len(objList))
#        
#        freeze_support() #prevent multiprocessing from freezing
#        with Pool(nProcesses) as pool:
#            res = pool.map(applyMedianFilter, objList)
#            
#        self._medianVelocityFrame   = res[0]
#        self._medianMagnitudeFrame  = res[1]
#        self._medianRMSSTD          = res[2]
        
        
        #Either applies a gaussian smoothing filter or a median filter.
        #NOTE: the gaussian smoothing is not very reliable, should only
        #Be used for testing.
        gaussianSmoothing = self._readFromSettings('gaussianSmoothing')
        if gaussianSmoothing:
            #Find sigma from FWHM and median diameter in settings
            filterRadius    = int(diameter / 2.355)
            self._medianVelocityFrame   = gaussian_filter(meanVelocityFrame,
                                                          filterRadius)
            self._medianMagnitudeFrame  = gaussian_filter(meanMagnitudeFrame,
                                                          filterRadius)
            self._medianRMSSTD          = gaussian_filter(rmsSTD,
                                                          filterRadius)
        
        else:
            
            self._medianVelocityFrame   = scipy.signal.medfilt2d(
                                                        meanVelocityFrame,
                                                        diameter)
        
            self._medianMagnitudeFrame  = scipy.signal.medfilt2d(
                                                        meanMagnitudeFrame,
                                                        diameter)
            self._medianRMSSTD          = scipy.signal.medfilt2d(
                                                        rmsSTD,
                                                        diameter)
        
        
        
    def _subtractMedian(self):
        '''Find and subtract the median-filtered mean velocity frame from
        all velocity frames.'''
        
        velocityFrames                  = np.asarray(
                                        self._selmaDicom.getVelocityFrames())
        self._correctedVelocityFrames   = (velocityFrames -
                                        self._medianVelocityFrame)

    #def _estimateVelocitySTD(self):
        """ Estimate the spatial standard deviation of the noise in the 
        velocity maps. Using iterative standard deviation estimations, outliers
        in the distribution (vessels) are removed by decreasing the cutoff 
        value. Once the standard deviation converges, it is assumed only noise
        is present in the distribution, resulting in an estimate for the 
        spatial standard deviation. 
        
        This function has been successfully implemented in the Basal Ganglia,
        and Semioval Centre where it is assumed that the noise in the velocity
        is normally distributed. 
        """
        
        #SD_factor = 3.5 # value derived from simulated data
        
        #meanVelocity    = np.mean(self._correctedVelocityFrames, axis = 0)

        #voxel_coordinates = np.where(self._mask == 1)
        
        #VelocityData = np.zeros((1,len(voxel_coordinates[0])))
 
        #for j in range(0,len(voxel_coordinates[0])):
        
            #VelocityData[0,j] = meanVelocity[voxel_coordinates[0][j],
                                                    #voxel_coordinates[1][j]]
            
        #CONVERGED = 0;
        #MAXRUNS = 100;
        #iRun = 0;
        #SD_init = np.std(VelocityData)
        #SD_prev = SD_init
        
        #while (not CONVERGED) and (iRun < MAXRUNS):
            
            #VelocityData_dummy = VelocityData
            #outlier_indices = np.where(abs(VelocityData) > 
                                       #(SD_factor * SD_prev))
            #VelocityData_dummy = np.delete(VelocityData_dummy,outlier_indices)
            #SD_curr = np.std(VelocityData_dummy)
            
            #if abs(SD_curr - SD_prev) < 10 * np.finfo(float).eps:
                
                #CONVERGED = 1;
                
            # Update counters/ stats
            #iRun = iRun + 1
            #SD_prev = SD_curr
            
        #self._velocitySTD = SD_curr
        
            
    def _SNR(self):
        """Calculates the SNR in the velocity frames. This is done in the 
        following manner:
           
            First the velocity frames are converted to phase frames
            Next, the phase and magnitude frames are converted to a complex
                signal from which the standard deviation in the real and 
                imaginary component are calculated.
            Next, the root mean square of these standard deviations is 
            obtained and a median-filter is applied.
            Next, the SNR in the magnitude frames is found.
            Lastly, the SNR in the velocity frames is calculated. 
            
        NEW APPROACH:
            
            Scale the corrected velocity maps with the converged standard 
            deviation obtained during the iterative outlier removal.
        """
    
        magnitudeFrames     = np.asarray(
                                    self._selmaDicom.getMagnitudeFrames())
        magnitudeSNR        = div0(magnitudeFrames,
                                   self._medianRMSSTD)
        venc                = self._selmaDicom.getTags()['venc']

        self._magnitudeSNR = magnitudeSNR
        
        if self._readFromSettings('BasalGanglia'):
        
            self._magnitudeSNRMask = (np.mean(magnitudeSNR, axis = 0) > 2).astype(np.uint8)
            
        elif self._readFromSettings('MiddleCerebralArtery'):
            
            self._magnitudeSNRMask = (np.mean(magnitudeSNR, axis = 0) > 10).astype(np.uint8)
               
        self._velocitySTD   = venc / np.pi * div0(1, magnitudeSNR)
        self._velocitySNR   = np.mean(div0(self._correctedVelocityFrames,
                                                self._velocitySTD), axis=0)  

    def _findSignificantFlow(self):
        """Uses the velocity SNR to find vessels with significant velocity:
            
            The threshold for significant flow is lower in the Basal Ganglia
            because of the overestimation of the SNR in the Basal Ganglia due
            to Rician noise floor effects and the lower T2* compared to the
            Semioval Centre. Therefore the relative threshold needed for 
            detecting 'significant flow' is lower.
        
        """
 
        # Derived from PULSATE data sqrt(mean RR interval/single shot time)
        PULSATEFactor = 2.9085772172269087 
        CADASILFactor = 2.75

        RR_interval         = self._selmaDicom.getTags()['R-R Interval']
        TFE                 = self._selmaDicom.getTags()['TFE']
        TR                  = self._selmaDicom.getTags()['TR']
        Temporal_resolution = self._selmaDicom.getTags()['Temporal resolution']
        
        if RR_interval == 0:
            
            NoiseFactor = PULSATEFactor
            
        else:

            NoiseFactor = np.sqrt(RR_interval/Temporal_resolution)
        
        sigma               = self._getSigma() * (PULSATEFactor/NoiseFactor)
        #sigma               = self._getSigma()
        
        if not self._readFromSettings('SemiovalCentre'):
        
            self._sigFlowPos    = (self._velocitySNR > sigma).astype(np.uint8) * self._magnitudeSNRMask
            self._sigFlowNeg    = (self._velocitySNR < -sigma).astype(np.uint8) * self._magnitudeSNRMask
            
        else:
            
            self._sigFlowPos    = (self._velocitySNR > sigma).astype(np.uint8)
            self._sigFlowNeg    = (self._velocitySNR < -sigma).astype(np.uint8)

        self._sigFlow       = self._sigFlowNeg + self._sigFlowPos  
  
    def _removeZeroCrossings(self):
        """Removes all vessels where the flow changes sign."""
        
        # velocityFrames  = np.asarray(
        #                     self._selmaDicom.getVelocityFrames())
        # signs           = np.sign(velocityFrames)
        
        signs           = np.sign(self._correctedVelocityFrames)
        signdiff        = np.diff(signs, axis=0) 
        noZeroCrossings = np.sum(np.abs(signdiff), axis=0) == 0
        
        self._sigFlowPos *= noZeroCrossings
        self._sigFlowNeg *= noZeroCrossings
        self._sigFlow    *= noZeroCrossings
        
                
    def _removeGhosting(self):
        """
        Creates a ghostingmask that can be used to subtract the areas 
        around bright vessels from the main mask.
        
        This mask is found as follows:
            
        Get xth percentile of vessels, read x from settings
        Cluster the bright vessels
        Go over each cluster and decide what size it is
            < noVesselThresh                        -> Ignore
            > noVesselTresh & < smallVesselThresh   -> Small exclusion zone
            > noVesselTresh & > smallVesselThresh   -> Large exclusion zone
        Create exclusion zone by finding the left, right , top , and bottom 
            most voxels and adding the exclusion buffers 
        Add exclusion zone to ghostingMask
                    
        
        """

        doGhosting      = self._readFromSettings('doGhosting')
        if not doGhosting:
            self._ghostingMask = np.zeros(self._mask.shape)
            return
        
        #Read from settings
        percentile          = self._readFromSettings('brightVesselPerc')
        
        noVesselThresh      = self._readFromSettings('noVesselThresh')
        smallVesselThresh   = self._readFromSettings('smallVesselThresh')
        
        smallVesselExclX    = self._readFromSettings('smallVesselExclX')
        smallVesselExclY    = self._readFromSettings('smallVesselExclY')
        
        largeVesselExclX    = self._readFromSettings('largeVesselExclX')
        largeVesselExclY    = self._readFromSettings('largeVesselExclY')
        
        #Remove sharp edges from mean magnitude frame.
        magnitude       = self._selmaDicom.getMagnitudeFrames()
        meanMagnitude   = np.mean(magnitude, axis = 0)
        medianMagnitude = self._medianMagnitudeFrame
        meanMagnitude   -= medianMagnitude
        
        #Find threshold for 'bright' vessels and mask them.
        meanMagNonzero  = np.abs(meanMagnitude[np.nonzero(meanMagnitude)])
        threshold       = np.percentile(meanMagNonzero, percentile*100)
        brightVesselMask= (np.abs(meanMagnitude) > threshold)
        brightVesselMask= brightVesselMask.astype(np.uint8)
        
        #Cluster the bright vessels
        nClusters, clusters = cv2.connectedComponents(brightVesselMask)
        ghostingMask    = np.zeros(meanMagnitude.shape)
        
        #Go over all the clusters and add to ghostingMask
        for idx in range(1, nClusters):     #skip 0, that's the background
            cluster = clusters == idx
            size    = np.sum(cluster)
            
            #If the cluster is too small, ignore
            if size <= noVesselThresh:
                continue
            
            #find left, right, top and bottom of cluster
            clusterCoords   = np.nonzero(cluster)
            left            = np.min(clusterCoords[1])
            right           = np.max(clusterCoords[1])
            top             = np.min(clusterCoords[0])
            bottom          = np.max(clusterCoords[0])
            
            #Small Vessel
            if size <= smallVesselThresh:
                
                #add buffer to left right, extend along y axis
                newLeft         = int(max(left      - smallVesselExclX,
                                      0))
                newRight        = int(min(right     + smallVesselExclX,
                                      meanMagnitude.shape[0] ))
                newTop          = int(max(top       - smallVesselExclY,
                                      0))
                newBottom       = int(min(bottom    + smallVesselExclY,
                                      meanMagnitude.shape[1]))
                
            #Large Vessel                
            else:
                #add buffer to left right, extend along y axis
                
                #Expand window with values from settings
                newLeft         = int(max(left      - largeVesselExclX,
                                      0))
                newRight        = int(min(right     + largeVesselExclX,
                                      meanMagnitude.shape[0] ))
                newTop          = int(max(top       - largeVesselExclY,
                                      0))
                newBottom       = int(min(bottom    + largeVesselExclY,
                                      meanMagnitude.shape[1]))
                
            #increase cluster size
            exclZone        = np.zeros(cluster.shape)
            exclZone[newTop : newBottom, newLeft : newRight] = 1
            
            #Update the ghostingMask
            ghostingMask += exclZone
        
        
        #store ghosting mask
        ghostingMask        = ghostingMask > 0
        self._ghostingMask  = ghostingMask.astype(np.uint8)
#        self._signalObject.sendVesselMaskSignal.emit(self._ghostingMask)
      
    def _removeOuterBand(self):
        """
        Creates an exclusion mask around the outer edges of the image with a 
        certain width.
        """
        
        ignoreOuterBand         = self._readFromSettings('ignoreOuterBand')
        self._outerBandMask     = np.zeros(self._mask.shape)
        if not ignoreOuterBand:
            
            self._outerBandMask     = np.zeros(self._mask.shape) + 1
            
            return
        
        band                            = 80    #TODO, get from settings
        # self._outerBandMask[:band, :]   = 1
        # self._outerBandMask[:, :band]   = 1
        # self._outerBandMask[-band:, :]  = 1
        # self._outerBandMask[:, -band:]  = 1
        
        _,th = cv2.threshold(self._medianMagnitudeFrame.astype(np.uint8),0,
                               1,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        kernel = np.ones((band, band), np.uint8)
        self._outerBandMask = cv2.erode(th,kernel)
        
    def _updateMask(self):
        """
        Removes the exclusion zones found in removeGhosting and 
        removeNonPerpendicular from the mask.
        
        Sends the updated mask to the GUI.
        """

        mask            = self._mask.astype(bool)
        ghost           = self._ghostingMask.astype(bool)
        outer           = self._outerBandMask.astype(bool)
        
        #Make mask without ghosting
        ghost           = ghost * mask
        maskMinGhost    = mask  ^ ghost
        
        #Make mask without outer edge
        outer           = (outer == False) * mask
        maskMinOuter    = mask  ^ outer
        
        #Combine all masks
        mask            = maskMinGhost & maskMinOuter
        
        self._mask = mask.astype(np.uint8)
        self._signalObject.sendMaskSignal.emit(self._mask)

    
    def _applyT1Mask(self):
        """First normalises, then applies the T1 mask (if any) to the 
        sigFlowPos, sigFlowNeg and sigFlow arrays."""
        mask = self._mask
        
        if mask is None:
            self._signalObject.errorMessageSignal.emit("No mask loaded.")
            return
        
        mask = mask.astype(bool) #prevent casting errors
        self._sigFlowPos *= mask
        self._sigFlowNeg *= mask
        self._sigFlow    *= mask
    
        
    def _findSignificantMagnitude(self):
        """
        Makes masks for all vessels with:
            -Positive magnitude
            -Negative magnitude
            -Isointense magnitude
        """        
   
        magnitudeFrames     = self._selmaDicom.getMagnitudeFrames()
        meanMagnitude       = np.mean(magnitudeFrames, axis = 0)
        sigma               = self._getSigma()
        
#        medianMagnitude     = scipy.signal.medfilt2d(meanMagnitude,
#                                                     self._medianDiameter)
        
        self._sigMagPos     = (meanMagnitude -
                               self._medianMagnitudeFrame -
                               sigma*self._medianRMSSTD
                                ) > 0
        self._sigMagPos     = self._sigMagPos.astype(np.uint8)
        
        self._sigMagNeg     = (meanMagnitude -
                               self._medianMagnitudeFrame +
                               sigma*self._medianRMSSTD
                                ) < 0
        self._sigMagNeg     = self._sigMagNeg.astype(np.uint8)
        
        #self._sigMagIso = self._sigFlow - self._sigMagNeg - self._sigMagPos
        
        # Consistent with MATLAB
        self._sigMagIso = (self._sigMagPos == 0) * (self._sigMagNeg == 0)
        self._sigMagIso = (self._sigMagIso > 0).astype(np.uint8)

    def _clusterVessels(self):
        
        """
        Function moved to SELMADataClustering for clarity
        """
 
        SELMADataClustering.clusterVessels(self)    
        
    def _removeNonPerpendicular(self):
        
        """
        Finds the non-perpendicular vessels and removes them. Algorithm works
        as follows:
            -Rescale magnitude image
            -Iterate over clusters:
                -if only posivitve mag. clusters: select for those
                -Find centre of cluster
                -Select window around cluster
                -Threshold based on centre intensity
                -Find connected components in thresholded window
                -Take the one closest to the centre
                -Find contour of component
                -Fit ellipse
                -Determine ratio major/minor axis
                -Remove cluster based on ratio
        
        """
      
        #if not self._readFromSettings('removeNonPerp'):
            
            #self._perp_clusters = []
            #self._non_perp_clusters = []
            #self._Noperp_clusters = []
    
            #return 
        
        self._non_perp_clusters = []
        self._perp_clusters = []
        self._axes_ratio = []
        
        # onlyMPos            = self._readFromSettings('onlyMPos')
        minScaling          = self._readFromSettings('minScaling')
        maxScaling          = self._readFromSettings('maxScaling')
        winRad              = int(self._readFromSettings('windowSize'))
        magnitudeThresh     = self._readFromSettings('magnitudeThresh')
        ratioThresh         = self._readFromSettings('ratioThresh')
        
        meanMagnitude   = np.mean(self._selmaDicom.getMagnitudeFrames(),
                                  axis = 0)
        stdMagnitude    = np.std(self._selmaDicom.getMagnitudeFrames())
        # stdMagnitude_MATLAB    = np.std(meanMagnitude)
        
        # MATLAB determines the std using the mean magnitude frame averaged
        # over the entire cardiac cycle (spatial variance). SELMA determines 
        # the std using all magnitude frames of the entire cardiac cycle
        # (temporal variance). The difference in std is about 1-2% between the
        # two implementations and has almost no effect on the amount of 
        # detected vessels. 
        
        # meanVelocity    = np.mean(self._correctedVelocityFrames, axis = 0)
        
        #Rescale magnitude image
        meanMeanMag     = np.mean(meanMagnitude)
        minMagnitude    = meanMeanMag - minScaling * stdMagnitude
        maxMagnitude    = meanMeanMag + maxScaling * stdMagnitude
        scaledMagnitude = ((meanMagnitude - minMagnitude) / 
                           (maxMagnitude - minMagnitude))   
        scaledMagnitude[scaledMagnitude > 1] = 1
        scaledMagnitude[scaledMagnitude < 0] = 0
           
        for idx, cluster in enumerate(self._clusters):
           
            if not np.size(np.where(cluster)[0]) > 2: 
                
                self._axes_ratio.append(1)
            
                self._perp_clusters.append(self._clusters[idx])
                
                continue
            
            # Check if cluster is larger than 2 voxels. If not, assume it 
            # is a round vessel
        
            #find centre coordinate of cluster (row column)
            clusterCoords   = np.nonzero(cluster)
            centre          = [int(np.mean(clusterCoords[0]) + 0.5),
                               int(np.mean(clusterCoords[1]) + 0.5)] 
            
            # int() always rounds down regardless of decimal value. This 
            # creates unintended behaviour where centre coordinates could
            # be off by 1 pixel. This is fixed by adding 0.5 to ensure
            # rounding is always correct
            
            #Get window around cluster in magnitude image
            magWindow       = scaledMagnitude[centre[0] - winRad:
                                              centre[0] + winRad,
                                              centre[1] - winRad:
                                              centre[1] + winRad ]
            
            "Attempt to correct for inconsistent remove non-perpendicular"
            "behaviour"
            # Get window around cluster in flow image 
            # flowWindow       = self._sigFlowPos[centre[0] - winRad:
            #                                   centre[0] + winRad,
            #                                   centre[1] - winRad:
            #                                   centre[1] + winRad ]
                
            #Threshold window to gain magnitude clusters of bright voxels
            threshold       = scaledMagnitude[centre[0], centre[1]]
            threshold       *= magnitudeThresh         
            magWindowThresh = (magWindow >= threshold).astype(np.uint8)
            
            # Comment out flowWindow for old version of remove non-perp
            
            blobWindow = magWindowThresh #* flowWindow 
            
            #Find cluster closest to centre
            ncomp, labels   = cv2.connectedComponents(blobWindow)
            distances   = []
            for n in range(1, ncomp):
                distances.append(
                    np.sqrt(
                        (np.mean(np.nonzero(labels == n)[0]) - winRad)**2 +
                        (np.mean(np.nonzero(labels == n)[1]) - winRad)**2))
            blob = labels == np.argmin(distances) + 1
            
            # New attempt at determining blob shape using regionprops. Now
            # more in line with MATLAB implementation. However, it is not 
            # exactly the same. Edge cases exist where the axes ratio 
            # in MATLAB is < 2 but in SELMA it is > 2.
                
            blob_stats = measure.regionprops_table(blob.astype(np.uint8),
                                                   properties=('centroid',
                                                   'minor_axis_length',
                                                   'major_axis_length'))
            
            minorRad = blob_stats['minor_axis_length'][0]
            majorRad = blob_stats['major_axis_length'][0]
            
            self._axes_ratio.append(majorRad/minorRad)
                          
            if majorRad / minorRad > ratioThresh:
                
                self._non_perp_clusters.append(self._clusters[idx])
                
            else:
                
                self._perp_clusters.append(self._clusters[idx])

        self._Noperp_clusters = len(self._perp_clusters)
                                         
    def _deduplicateVessels(self):
        
        """         
            Take the first voxel of each cluster
            check whether any of them are <6 pixels apart
            if so, remove both clusters
        """

        # Added clauses for seperate scenarios when different settings are
        # turned on or off. This ensures the correct clusters are passed
        # through to the end

        if not self._readFromSettings('removeNonPerp'):
            
            clusters = self._clusters
            
        if self._readFromSettings('removeNonPerp'):
            
            clusters = self._perp_clusters

        if not self._readFromSettings(
                'deduplicate') and not (
                    self._readFromSettings('removeNonPerp')):
            
            self._cluster_vessels = []
            
            return
        
        if not self._readFromSettings(
                'deduplicate') and self._readFromSettings('removeNonPerp'):
            
            self._clusters = self._perp_clusters
            self._cluster_vessels = []
            
            return
           
        self._lone_vessels = []
        self._cluster_vessels = []
        
        dedupRange  = self._readFromSettings('deduplicateRange')
        
        #First make a list of all the voxels with the highest velocity per
        #cluster
        meanVelocity    = np.mean(self._correctedVelocityFrames,
                                  axis = 0)
        voxels  = []

        iMBlob_array = np.zeros((1,len(clusters)))
        
        iMblob          = self._posMagClusters - self._negMagClusters

        i = 0

        for cluster in clusters:
            
            pixels      = np.nonzero(cluster)
            velocities  = np.abs(meanVelocity[pixels])
            indexes     = np.argsort(velocities)
            x,y         = np.transpose(pixels)[indexes[-1]]
   
            self._lone_vessels.append(cluster)
            
            voxels.append([x,y])
                
            iMBlob_array[0,i] = int(iMblob[x,y]) # iMblob only approach
            
            i = i + 1

        if voxels == []:
            return
        
        voxels, order  = np.unique(np.asarray(voxels), axis = 0, return_index
                                   = True)
        voxels = voxels[np.argsort(order)]

        if not self._readFromSettings('SemiovalCentre'):
            
            DuplicateVessels = []
            
            _,uniq_idx,counts = np.unique(iMBlob_array,return_index = True, 
                                          return_counts = True)
            
            if np.max(counts) > 1:
            
                OverlappingBlobs = iMBlob_array[0,uniq_idx[np.where(counts 
                                                                    > 1)]]
            
                for blob in OverlappingBlobs:
                
                    temp_vessels = np.where(iMBlob_array == blob)[1]
                    
                    i = 0
                    
                    temp_velocities = np.zeros((1,len(temp_vessels)))
                    
                    for perforator in temp_vessels:
                        
                        temp_velocities[0,i] = meanVelocity[voxels[perforator]
                                                            [0],
                                                            voxels[perforator]
                                                            [1]]
           
                        i = i + 1
                    
                    DuplicateVessels.append(temp_vessels[np.where(
                        temp_velocities != np.max(temp_velocities[0,:]))[1]])
                
            # DuplicateVessels are duplicate magnitude blobs with a lower 
            # velocity
         
            if DuplicateVessels != []:
                
                idx = np.sort(np.concatenate(DuplicateVessels))
                
                #Remove the selected clusters
                for i, clusterNum in enumerate(idx):
                
                    self._cluster_vessels.append(self._lone_vessels[clusterNum 
                                                                    - i])
                
                    del(self._lone_vessels[clusterNum - i])
                
            else: # Test the removal of duplicate vessels based on iMblob
                
                idx = []
            
            voxels = np.delete(voxels,idx,0)
        
        #Next, create matrix of the distances between all these voxels
        x       = np.repeat(np.reshape(voxels[:,0],(-1,1)), len(voxels), 1)
        xArr    = (x - np.transpose(x))**2
        
        y       = np.repeat(np.reshape(voxels[:,1],(-1,1)), len(voxels), 1)
        yArr    = (y - np.transpose(y))**2
        
        distances   = np.sqrt(xArr + yArr)
        selection   = np.tril((distances != 0) * (distances < dedupRange))
        idx         = np.unique(np.nonzero(selection))
        
        DuplicateVessels = []
        
        for blob in idx:
            
            temp_idx = np.where(distances[:,blob] < 6)[0]
            
            i = 0
            
            temp_velocities = np.zeros((1,len(temp_idx)))
        
            for perforator in temp_idx:
                
                temp_velocities[0,i] = abs(meanVelocity[voxels[perforator][0],
                                                    voxels[perforator][1]])
   
                i = i + 1
            
            DuplicateVessels.append(temp_idx[np.where(
                temp_velocities != np.max(temp_velocities[0,:]))[1]])
 
        if DuplicateVessels != []:
            
            idx = np.unique(np.sort(np.concatenate(DuplicateVessels)))
            
            #Remove the selected clusters
            for i, clusterNum in enumerate(idx):

                self._cluster_vessels.append(self._lone_vessels[clusterNum - 
                                                                i])
            
                del(self._lone_vessels[clusterNum - i])
                
        self._clusters = self._lone_vessels
        
    def _createVesselMask(self):
        """
        Iterates over the clusters found in _clusters and creates
        a mask of all the vessels.
        """
        
        mask = np.zeros(self._mask.shape,
                        dtype = np.int32)
        
        for labels in self._clusters:
            mask += labels
        
        self._vesselMask        = mask.astype(bool)
             
    def _manualSelection(self):
        
        SELMADataSelection.SELMADataSelection.VesselSelection(self)
            
    def _calculateParameters(self):       
        """
        Function moved to SELMADataCalculate for clarity
        """
 
        SELMADataCalculate.calculateParameters(self)
        
    def _makeVesselDict(self):
        """Makes a dictionary containing the following statistics
        for each voxel in a vessel:
            -pixelID    (with arrays starting at 0)
            -row        (with arrays starting at 0)
            -column     (with arrays starting at 0)
            -clusternumber
            -VNeg       (true or false)
            -VPos       (true or false)
            -MPos       (true or false)
            -MIso       (true or false)
            -MNeg       (true or false)
            -Mean Magnitude
            -Magnitude STD
            -mean Velocity
            -Velocity STD
            -min Velocity
            -max Velocity
            -PI         (maxV - minV)/meanV
            -nPhases    (how many heart cycles)
            -iMblob     (magnitude clustering list)
            -Mag per cycle 
            -Velocity per cycle
            
        Additional dictionary is created with following data per scan:
            - No. detected vessels
            - No. MPos vessels
            - No. MNeg vessels
            - No. MIso vessels
            - No. perpendicular vessels
            - No. non-perpendicular vessels
            - No. lone vessels
            - No. cluster vessels
            - Vmean lone vessels
            - Vmean standard error from mean (SEM)
            - PI_norm lone vessels
            - PI_norm SEM
            - No. BG mask pixels"""

        self._vesselDict = dict()
        self._velocityDict = dict()        
        
        #Get some variables from memory to save time. 
        meanMagnitude   = np.mean(self._selmaDicom.getMagnitudeFrames(),
                                  axis = 0)
        meanVelocity    = np.mean(self._correctedVelocityFrames,
                                  axis = 0)
        magFrames       = np.asarray(self._selmaDicom.getMagnitudeFrames())
        
        iMblob          = self._posMagClusters - self._negMagClusters 

        meanMagnitudeSNR    = np.mean(self._magnitudeSNR, axis=0) * self._mask
        meanMagnitudeSNR    = meanMagnitudeSNR[np.nonzero(meanMagnitudeSNR)].mean()

        meanMagnitudeSNR_vessels    = np.mean(self._magnitudeSNR, axis=0) * self._vesselMask
        meanMagnitudeSNR_vessels    = meanMagnitudeSNR_vessels[np.nonzero(meanMagnitudeSNR_vessels)].mean()

        meanVelocitySNR    = np.abs(self._velocitySNR) * self._mask
        meanVelocitySNR    = meanVelocitySNR[np.nonzero(meanVelocitySNR)].mean()

        meanVelocitySNR_vessels    = np.abs(self._velocitySNR) * self._vesselMask
        meanVelocitySNR_vessels    = meanVelocitySNR_vessels[np.nonzero(meanVelocitySNR_vessels)].mean()

        #Keep track of the progress to emit to the progressbar
        i       = 0 
        # total   = np.sum(np.asarray(self._clusters * self._sigFlowPos))
        total   = np.sum(np.asarray(self._included_vessels))
        
        for idx, cluster in enumerate(self._included_vessels):
         
            #Sort pixels in cluster by mean velocity (largest to smallest)
            pixels      = np.nonzero(cluster)
            velocities  = np.abs(meanVelocity[pixels])
            indexes     = np.argsort(velocities)
            indexes     = indexes[::-1]    #largest to smallest            
            
            pixels      = np.transpose(pixels)
            
            for num, pidx in enumerate(indexes):
                x,y = pixels[pidx]
                value_dict = dict()
                value_dict['pixel']         = int(y*cluster.shape[-1] + x+1)
                value_dict['ir']            = int(x+1)
                value_dict['ic']            = int(y+1)
                value_dict['iblob']         = int(idx + 1)
                value_dict['ipixel']        = int(num + 1)
                value_dict['Vneg']          = round(self._sigFlowNeg[x,y],  4)
                value_dict['Vpos']          = round(self._sigFlowPos[x,y],  4)
                value_dict['Mpos']          = round(self._sigMagPos[x,y],   4)
                value_dict['Miso']          = round(self._sigMagIso[x,y],   4)
                value_dict['Mneg']          = round(self._sigMagNeg[x,y],   4)
                value_dict['meanMag']       = round(meanMagnitude[x,y],     4)
                value_dict['stdMagnoise']   = round(self._medianRMSSTD[x,y],4)
                value_dict['meanV']         = round(meanVelocity[x,y],      4)
                #value_dict['stdVnoise']     = round(np.mean(
                                                #self._velocitySTD[:,x,y]),  4)
                value_dict['minV']          = round(np.min(np.abs(
                    self._correctedVelocityFrames[:,x,y])),4)
                value_dict['maxV']          = round(np.max(np.abs(
                    self._correctedVelocityFrames[:,x,y])), 4)
                value_dict['PI']            = abs(round(div0(
                                             [(value_dict['maxV'] -
                                              value_dict['minV'])],
                                              value_dict['meanV'])[0],
                                                    4))
                value_dict['nPha']    = self._correctedVelocityFrames.shape[0]
                value_dict['imBlob']  = int(iMblob[x,y])
                
                
                #Magnitude per phase
                for num, value in enumerate(magFrames[:,x,y].tolist()):
                    num += 1
                    if num < 10:
                        numStr = '0' + str(num)
                    else:
                        numStr = str(num)
                        
                    value_dict['Mpha' + numStr] = round(value, 4)
                
                #Velocity per phase
                for num, value in enumerate(
                        self._correctedVelocityFrames[:,x,y].tolist()):
                    num += 1
                    if num < 10:
                        numStr = '0' + str(num)
                    else:
                        numStr = str(num)
                        
                    value_dict['Vpha' + numStr] = round(value, 4)
                
                #Add vesselinfo to vessel dictionary
                self._vesselDict[i] = value_dict
                
                #Emit progress to progressbar
                self._signalObject.setProgressBarSignal.emit(
                        int(100 * i / total))
                i+= 1
                
        'Additional dictionary is created below'

        velocity_dict = dict()
        velocity_dict['No. detected vessels']           = len(self._clusters)
        velocity_dict['No. MPos vessels']               = self._NoMPosClusters
        velocity_dict['No. MNeg vessels']               = self._NoMNegClusters
        velocity_dict['No. MIso vessels']               = self._NoMIsoClusters
        
        if self._readFromSettings('removeNonPerp'):
            
            velocity_dict['No. perpendicular vessels'] = self._Noperp_clusters
            velocity_dict['No. non-perpendicular vessels'] = len(
                                                    self._non_perp_clusters)
            
        if self._readFromSettings('deduplicate'):
            
            velocity_dict['No. lone vessels']     = len(self._lone_vessels)
            velocity_dict['No. cluster vessels']  = len(self._cluster_vessels)
            # velocity_dict['No. included vessels'] = len(
                                                    # self._included_vessels)
            # velocity_dict['Vmean lone vessels'] = round(self._Vmean, 4)
            # velocity_dict['PI_norm lone vessels'] = round(self._PI_norm, 4)
            
        # else:
            
        #     velocity_dict['No. vessels'] = len(self._lone_vessels)
        
        velocity_dict['No. included vessels']   = len(self._included_vessels)
        velocity_dict['Vmean vessels']          = round(self._Vmean, 4)
        velocity_dict['PI_norm vessels']        = round(self._PI_norm, 4)
        velocity_dict['median PI_norm vessels'] = round(self._PI_median_norm, 4)
        
        if not self._readFromSettings('MiddleCerebralArtery'):

            velocity_dict['Vmean SEM']              = round(self._allsemV, 4)
            velocity_dict['PI_norm SEM']            = round(self._allsemPI, 4)
            velocity_dict['median PI_norm SEM']     = round(self._allsemPI_median, 4)
            
        velocity_dict['No. BG mask pixels']     = sum(sum(self._mask == 1))
        
        velocity_dict['mean SNR magnitude mask'] = round(meanMagnitudeSNR, 4)
        velocity_dict['mean SNR magnitude vessels'] = round(meanMagnitudeSNR_vessels, 4)
        velocity_dict['mean SNR velocity mask'] = round(meanVelocitySNR, 4)
        velocity_dict['mean SNR velocity vessels'] = round(meanVelocitySNR_vessels, 4)
  
        self._velocityDict[0] = velocity_dict
        
        self._signalObject.setProgressBarSignal.emit(100)

 
        

    
        
    
        
        
        
        