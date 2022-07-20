#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SELMADicom`

"""


# ====================================================================
#IO

import pydicom
import numpy as np
import SELMAGUISettings
from PyQt5 import QtCore
# ====================================================================

class SELMADicom:
    """
    This class contains all methods concerning the handling of .dcm (Dicom)
    data. All the manufacturer specific information, such as keys, addresses
    etc. is managed here.
    """
    
    def __init__(self, dcmFilename):
        """Read the dicom header using pydicom. 
        Also extract the pixel array.
        Call the functions that initiate the Dicom."""
        
        self._dcmFilename   = dcmFilename
        self._DCM           = pydicom.dcmread(self._dcmFilename)

        self._tags          = dict()
        self._rawFrames     = self._DCM.pixel_array
        self._numFrames     = len(self._rawFrames)
        self._rescaleVelocity   = None
        
        #Get manufacturer
        self._findManufacturer()
        
        #find important Tags
        self._findRescaleValues()    
        self._findVEncoding()
        self._findFrameTypes()
        self._findPixelSpacing()     
        self._findNoiseScalingFactors()
        self._findTargets()
        
        #Get rescale values and apply
        self._rescaleFrames()
        
        #Sort the frames on their type
        self._orderFramesOnType()
    
        
    '''Public'''
    #Getter functions
    # ------------------------------------------------------------------    
    def getTags(self):
        return self._tags
  
    def getFrames(self):
        return self._rescaledFrames
    
    def getRawFrames(self):
        return self._rawFrames
    
    def getDCM(self):
        return self._DCM
    
    def getNumFrames(self):
        return self._numFrames
    
    def getVelocityFrames(self):

        if self._velocityFrames != []:
            return self._velocityFrames
        else:
            return self._makeVelocityFrames()[0]
    
    def getMagnitudeFrames(self):
        return self._magnitudeFrames
    
    def getModulusFrames(self):
        return self._modulusFrames
    
    def getRawVelocityFrames(self):
        if self._rawVelocityFrames != []:
            return self._rawVelocityFrames
        else:
            return self._makeVelocityFrames()[1]
    
    def getRawMagnitudeFrames(self):
        return self._rawMagnitudeFrames
    
    def getRawModulusFrames(self):
        return self._rawModulusFrames
    
    def getNoiseScalingFactors(self):
        return self._tags['R-R Interval'], self._tags['TFE'], self._tage['TR']
    
    def getPixelSpacing(self):
        return self._tags['pixelSpacing']

        
    
    #Setter functions
    # ------------------------------------------------------------------    
    
    def setVenc(self, venc):
        self._tags['venc'] = venc
        
        
    def setVelRescale(self, rescale):
        self._rescaleVelocity   = rescale
        self._rescaleVelocityFrames()
        
    '''Private'''
    # Setup data from .dcm header
    # ------------------------------------------------------------------    
    
    """Where to find the relevant dicom tags for different vendors.    
    
    Philips:
    Frame data stored in                                (5200, 9230) 
    Manufacturer stored in :                            (2005, 0014) 
    Manufacturer specific data stored in:               (2005, 140f)  
    Image Type stored in                                (0008, 0008)
    Image Types for the following frames:
        Modulus:    ['ORIGINAL', 'PRIMARY', 'M_PCA', 'M', 'PCA']
        Magnitude:  ['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE']
        Velocity:   ['ORIGINAL', 'PRIMARY', 'VELOCITY MAP', 'P', 'PCA']
    Rescale values stored in:
        Intercept:                                      (2005, 100d)
        Slope:                                          (2005, 100e)
    VEnc value stored at:
        vEncAddress                                     (0018, 9197)
        vEncMaxAddress                                  (0018, 9217)
    
    """
    
    def _findManufacturer(self):
        """Extract the manufacturer from the dicom"""

        self._tags['manufacturer'] = self._DCM[0x0008, 0x0070].value
    
    def _findRescaleValues(self):
        """Finds the rescale slope and intercept
        and applies it to the frames"""
        
        rescaleSlopes     = []
        rescaleIntercepts = []
        
        #Philips
        if 'philips' in self._tags['manufacturer'].lower():
            dcmFrameAddress             = 0x5200, 0x9230
            dcmPrivateCreatorAddress    = 0x2005, 0x140f
            dcmRescaleSlopeAddress      = 0x2005, 0x100E
            dcmRescaleInterceptAddress  = 0x2005, 0x100D
            
            
            for i in range(self._numFrames):
                rescaleSlope        = float(self._DCM[dcmFrameAddress][i]           
                                        [dcmPrivateCreatorAddress][0]      
                                        [dcmRescaleSlopeAddress].value)
                          
                rescaleIntercept    = float(self._DCM[dcmFrameAddress][i]           
                                        [dcmPrivateCreatorAddress][0]      
                                        [dcmRescaleInterceptAddress].value)
                
                rescaleSlopes.append(rescaleSlope)
                rescaleIntercepts.append(rescaleIntercept)



         #Other manufacturers
        #
        #
        #
    
        
        self._tags['rescaleSlopes']     = rescaleSlopes
        self._tags['rescaleIntercepts'] = rescaleIntercepts



    def _findVEncoding(self):
        """Gets the velocity encoding maximum in the z-direction from the DCM.
        It's assumed that this is constant for all frames."""
        
        
        #Standard value (see 
        #   https://dicom.innolitics.com/ciods/mr-spectroscopy/
        #   mr-spectroscopy-multi-frame-functional-groups/
        #   52009229/00189197/00189217
        
        try:
            dcmFrameAddress             = 0x5200, 0x9230
            vEncAddress                 = 0x0018, 0x9197
            vEncMaxAddress              = 0x0018, 0x9217
       
            venc = self._DCM[dcmFrameAddress] [0]       \
                            [vEncAddress]     [0]       \
                            [vEncMaxAddress].value

            #Adjust for units
            if self._checkVencUnit():
                venc /= 10
                            
            self._tags['venc'] = venc
            return
        except:
            pass
        
        
        #Specific attribute locations if the above doesn't work
        #Philips:
        
        if 'philips' in self._tags['manufacturer'].lower():
            vencAddress                 = 0x2001, 0x101A

            venc                        = self._DCM[vencAddress].value
            venc                        = venc[-1] 
        
        #Other manufacturers
        #...        
        
        
        #Adjust for units
        if self._checkVencUnit():
            venc /= 10
        
        #Write to tags
        self._tags['venc'] = venc
            
            
            
    def _findFrameTypes(self):
        """Find the frame types per manufacturer.
        Method differs for each manufacturer."""
        
        self._tags['frameTypes'] = []
        
        #Philips
        if 'philips' in self._tags['manufacturer'].lower():
            self._dcmFrameAddress             = 0x5200, 0x9230
            self._dcmPrivateCreatorAddress    = 0x2005, 0x140f
            self._dcmImageTypeAddress         = 0x0008, 0x0008
            
            for i in range(self._numFrames):
                frameType = self._DCM[self._dcmFrameAddress][i]                   \
                                [self._dcmPrivateCreatorAddress][0]               \
                                [self._dcmImageTypeAddress].value[2]
                self._tags['frameTypes'].append(frameType)
            
            
        #Other manufacturers
        #
        #
        #
        
    def _findPixelSpacing(self):
        """Find Pixel spacing in Dicom header, save it to the tags."""
        
        ps  = float(
            self._DCM.PerFrameFunctionalGroupsSequence[0].
            PixelMeasuresSequence[0].PixelSpacing[0])
        
        self._tags['pixelSpacing'] = ps
        
    def _findNoiseScalingFactors(self):
        """Find RR intervals and TFE in Dicom header, save it to the tags"""
 
        # Philips
        RR_interval = self._DCM.CardiacRRIntervalSpecified
        TFE = self._DCM.GradientEchoTrainLength
        TR = self._DCM[0x5200, 0x9229][0][0x0018, 0x9112][0][0x0018, 0x0080].value
        
        self._tags['R-R Interval'] = RR_interval
        self._tags['TFE'] = TFE
        self._tags['TR'] = TR
        
    def _findTargets(self):
        """
        Saves the manufacturer specific names for the phase, velocity,
        magnutide and modulus frames.
        
        """
        self._tags['targets'] = dict()
        
        #Philips
        if 'philips' in self._tags['manufacturer'].lower():
            self._tags['targets']['phase']      = 'PHASE'
            self._tags['targets']['velocity']   = 'VELOCITY'
            self._tags['targets']['magnitude']  = "M_FFE"
            self._tags['targets']['modulus']    = "M_PCA"
            
        
        #Siemens
        if 'siemens' in self._tags['manufacturer'].lower():
            self._tags['targets']['phase']      = 'P'
            self._tags['targets']['velocity']   = 'V'
            self._tags['targets']['magnitude']  = "MAG"
            self._tags['targets']['modulus']    = "M"
            
        
        #GE            
        if 'ge' in self._tags['manufacturer']:            
            self._tags['targets']['phase']      = 'Phase'
            self._tags['targets']['velocity']   = 'Velocity'
            self._tags['targets']['magnitude']  = "Magnitude"
            self._tags['targets']['modulus']    = "Modulus"
            
            
    
    # Apply changes to the frames
    # ------------------------------------------------------------------    

    def _rescaleFrames(self):
        ''' Applies the rescale slope and intercept to the frames. '''       

        self._rescaledFrames    = []
        for i in range(len(self._rawFrames)):
            rescaleSlope        = self._tags['rescaleSlopes'][i]
            rescaleIntercept    = self._tags['rescaleIntercepts'][i]
            
            rawFrame            = self._rawFrames[i]
            rescaledFrame       = (rawFrame - rescaleIntercept)/rescaleSlope
            
            self._rescaledFrames.append(rescaledFrame)
            
    def _rescaleVelocityFrames(self):
        '''
        Rescales only the velocity frames (if available).
        Called when manual rescale values are set.
        
        The rescaling assumes that the intercept is halfway between the min 
        and max.
        
        TODO: change from maxRaw to max. possible value (4096 or such)
        
        '''
        if len(self._velocityFrames) == 0:
            return
        
        minVel, maxVel  = self._rescaleVelocity
        minRaw          = np.min(self._rawVelocityFrames).astype(np.float)
        maxRaw          = np.max(self._rawVelocityFrames).astype(np.float)
        
        deltaVel        = np.abs(minVel - maxVel)
        deltaRaw        = np.abs(minRaw - maxRaw)
        slope           = deltaRaw / deltaVel
        intercept       = deltaRaw / 2 + minRaw
        
        self._velocityFrames    = (self._rawVelocityFrames - 
                                   intercept) / slope
        


    def _orderFramesOnType(self):
        """Uses the indices found in findFrameTypes to create an array for
        the magnitude, modulus, and velocity frames."""
        
        self._magnitudeFrames           = []
        self._rawMagnitudeFrames        = []
        self._modulusFrames             = []
        self._rawModulusFrames          = []
        self._velocityFrames            = []
        self._rawVelocityFrames         = []
        self._phaseFrames               = []
        self._rawPhaseFrames            = []
        
        frameTypes      = self._tags['frameTypes']
        targets         = self._tags['targets']
        
        # Fix for very rare bug in DICOM headers where certain frames could be
        # mislabelled. 
        #TODO add compatibility for other scanner manufacturers

        for idx in range(len(frameTypes)):
            
            if all(frameTypes[idx][0:3] not in mystring for mystring in targets.values()): #frameTypes[idx]
                
                tempFrameType = self._DCM[self._dcmFrameAddress][idx]                   \
                                [self._dcmPrivateCreatorAddress][0]               \
                                [self._dcmImageTypeAddress].value[3:5]
                
                if tempFrameType[1] in targets['magnitude']:
                    
                    frameTypes[idx] = targets['magnitude']
                    
                elif tempFrameType[1] in targets['modulus']:
                    
                    if tempFrameType[0] in targets['phase']:
                
                        frameTypes[idx] = targets['phase']
                        
                    else:
                        
                        frameTypes[idx] = targets['modulus']
                        
                else:
                    
                    frameTypes[idx] = targets['velocity']
    
        for idx in range(self._numFrames):
                        
            if targets['velocity'] in frameTypes[idx]:
                self._velocityFrames.append(self._rescaledFrames[idx])
                self._rawVelocityFrames.append(self._rawFrames[idx])
                
            elif targets['magnitude'] in frameTypes[idx]:
                self._magnitudeFrames.append(self._rescaledFrames[idx])
                self._rawMagnitudeFrames.append(self._rawFrames[idx])
                
            elif targets['modulus'] in frameTypes[idx]:
                self._modulusFrames.append(self._rescaledFrames[idx])
                self._rawModulusFrames.append(self._rawFrames[idx])
                
            elif targets['phase'] in frameTypes[idx]:
                self._phaseFrames.append(self._rescaledFrames[idx])
                self._rawPhaseFrames.append(self._rawFrames[idx])
            
            
        self._magnitudeFrames       = np.asarray(self._magnitudeFrames)
        self._rawMagnitudeFrames    = np.asarray(self._rawMagnitudeFrames)
        self._modulusFrames         = np.asarray(self._modulusFrames)
        self._rawModulusFrames      = np.asarray(self._rawModulusFrames)
        self._velocityFrames        = np.asarray(self._velocityFrames)
        self._rawVelocityFrames     = np.asarray(self._rawVelocityFrames)
        self._phaseFrames           = np.asarray(self._phaseFrames)
        self._rawPhaseFrames        = np.asarray(self._rawPhaseFrames)
    
    def _makeVelocityFrames(self):
        '''
        Construct velocity frames out of the phase frames if any phase frames
        exist. Formula: v = phase * venc / pi
        
        Frames are not stored as member objects, but returned when 
        getVelocityFrames is called. This enables later manual rescaling.
        
        TODO: add rescaling
        '''
        
        if len(self._phaseFrames) > 0 and len(self._velocityFrames) == 0:
            
            venc = self._tags['venc']
            
            #Check if the velocity frames aren't accidentally stored as phase
            
            if np.round(np.max(self._phaseFrames), 1) == venc and \
               np.round(np.min(self._phaseFrames), 1) == -venc:
                   return [self._phaseFrames, self._rawPhaseFrames]
            
            #Else, compute velocity frames from the phaseFrames
            
            #check for manual rescale. If this exists, the phase frames are 
            #assumed to be velocity frames and will be rescaled from the raw
            #frames.
            if self._rescaleVelocity is not None:
                minVel, maxVel  = self._rescaleVelocity
                minRaw          = np.min(self._rawPhaseFrames).astype(
                                                                    np.float)
                maxRaw          = np.max(self._rawPhaseFrames).astype(
                                                                    np.float)
                
                deltaVel        = np.abs(minVel - maxVel)
                deltaRaw        = np.abs(minRaw - maxRaw)
                slope           = deltaRaw / deltaVel
                intercept       = deltaRaw / 2 + minRaw
                
                velocityFrames  = (self._rawPhaseFrames - intercept) / slope

                return  [velocityFrames, self._rawPhaseFrames]
                
            else:
                frames      = self._phaseFrames * venc / np.pi
                rawFrames   = self._rawPhaseFrames * venc / np.pi

                return [frames, rawFrames]
                
                
                
                
    def _checkVencUnit(self):
        """Check the settings to find the 'mmVenc' value"""
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        settings            = QtCore.QSettings(COMPANY, APPNAME)
        
        return settings.value('mmVenc') == "true"
    
        