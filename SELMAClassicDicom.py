#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SELMAClassicDicom`

"""


# ====================================================================
#IO
import SELMADicom
import pydicom
import numpy as np
import os

# ====================================================================

class SELMAClassicDicom(SELMADicom.SELMADicom):
    """
    This class contains all methods concerning the handling of a classic 
    .dcm (Dicom) file. All the manufacturer specific information, such as keys,
    addresses etc. is managed here.
    
    This class assumes the following:
        the manufacturer and velocity encoding value are the same for 
        all files in the directory.
    """
    
    def __init__(self, dcmFilenames):
        """Read the dicom header using pydicom. 
        Also extract the pixel array.
        Call the functions that initiate the Dicom."""
 
        self._dcmFilenames    = dcmFilenames
        
        self._tags              = dict()
        self._DCMs              = list()
        self._numFrames         = len(self._dcmFilenames)
        self._rescaleVelocity   = None
        
        # load the dicoms
        #Iterate over the dicom files in the directory.
        rawFrames           = []
        for filename in self._dcmFilenames:
            DCM             = pydicom.dcmread(filename)
            self._DCMs.append(DCM)
            rawFrames.append(DCM.pixel_array)
            
        self._rawFrames     = np.asarray(rawFrames)
            
        #Get manufacturer
        self._findManufacturer()
        
        #find important Tags
        self._findVEncoding()
        self._findRescaleValues()    
        self._findFrameTypes()
        self._findPixelSpacing()   
        self._findNoiseScalingFactors()
        self._findTargets()
        
        #Get rescale values and apply
        self._rescaleFrames()

        #Sort the frames on their type
        self._orderFramesOnType()
        
    def getNoiseScalingFactors(self):
         return self._tags['R-R Interval'], self._tags['TFE'], self._tags['TR'], self._tags['Temporal resolution']
    
    ##############################################
    #Overridden functions
    
    '''Private'''
    
    def _findManufacturer(self):
        """Extract the manufacturer from the dicom. It's assumed that every
        dicom file in the list has the same manufacturer.
        
        Manufacturer is stored as a lower script version.
        """

        self._tags['manufacturer'] = self._DCMs[0][0x8, 0x70].value.lower()
    
    def _findRescaleValues(self):
        """Finds the rescale slope and intercept
        and applies it to the frames"""
        
        
        rescaleSlopes     = []
        rescaleIntercepts = []
            
            
        #Philips
        if 'philips' in self._tags['manufacturer']:
            dcmRescaleInterceptAddress  = 0x2005, 0x100D
            dcmRescaleSlopeAddress      = 0x2005, 0x100E
            
            try: 
                for i in range(self._numFrames):
                    rescaleSlope        = float(self._DCMs[i]
                                        [dcmRescaleSlopeAddress].value)
                    rescaleIntercept    = float(self._DCMs[i]
                                        [dcmRescaleInterceptAddress].value)
                
                    rescaleSlopes.append(rescaleSlope)
                    rescaleIntercepts.append(rescaleIntercept)
            except:
                    address1                    = 0x0040, 0x9096
                    dcmRescaleInterceptAddress  = 0x0040, 0x9224
                    dcmRescaleSlopeAddress      = 0x0040, 0x9225
                    
                    for i in range(self._numFrames):
                        rescaleSlope        = float(self._DCMs[i][address1][0][dcmRescaleSlopeAddress].value)
                        rescaleIntercept    = float(self._DCMs[i][address1][0][dcmRescaleInterceptAddress].value)
                    
                        rescaleSlopes.append(rescaleSlope)
                        rescaleIntercepts.append(rescaleIntercept)


        #Siemens
        if 'siemens' in self._tags['manufacturer']:
            #Try to find the rescale values in the slices. If not available,
            #Also try to calculate the value for venc
            
            dcmRescaleInterceptAddress  = 0x0028, 0x1052
            dcmRescaleSlopeAddress      = 0x0028, 0x1053

            for i in range(self._numFrames):
                
                try:
                    
                    if self._DCMs[i][0x8, 0x8].value[2] == 'V' or \
                        self._DCMs[i][0x8, 0x8].value[2] == 'P':
                    
                            venc    = self._tags['venc'] 
                            minVal  = np.min(self._rawFrames[i])
                            maxVal  = np.max(self._rawFrames[i])
                            
                            slope   = (maxVal - minVal) / ( 2 * venc) 
                            intercept   = (maxVal - minVal) / 2 + minVal
                            
                            rescaleSlopes.append(slope)
                            rescaleIntercepts.append(intercept)
                    
                    else:
                        
                        rescaleSlopes.append([])  
                        rescaleIntercepts.append([])
                        
                except:
                #If no rescale values can be found, the values can be 
                #calculated as such: 
                #Set the rescale slope and intersect to go from -venc to 
                #venc. Only if the frame is velocity or phase.
                
                #Note: This assumes that the values in the frame do 
                #actually range from -venc to venc. If this is not the 
                #case, the calculated velocities might be off slightly.
                #The rescaling assumes that the intercept is halfway between 
                #the min and max.
                
                #TODO: find the min and max possible raw values and not just
                #the ones that occur. Look into how many bits are used to store
                #data per voxel.
                #16 bits -> 4096?
                
                    if self._DCMs[i][0x8, 0x8].value[2] == 'V' or \
                        self._DCMs[i][0x8, 0x8].value[2] == 'P':
                    
                            venc    = self._tags['venc'] 
                            minVal  = np.min(self._rawFrames[i])
                            maxVal  = np.max(self._rawFrames[i])
                            
                            slope   = (maxVal - minVal) / ( 2 * venc) 
                            intercept   = (maxVal - minVal) / 2 + minVal
                            
                            rescaleSlopes.append(slope)
                            rescaleIntercepts.append(intercept)
                    
                    else:
                        
                        rescaleSlopes.append([])  
                        rescaleIntercepts.append([])
                


        # GE
        if 'ge' in self._tags['manufacturer']:
            #Try to find the rescale values in the slices. If not available,
            #Also try to calculate the value for venc
            
            dcmRescaleInterceptAddress  = 0x0028, 0x1052
            dcmRescaleSlopeAddress      = 0x0028, 0x1053

            for i in range(self._numFrames):
                
                try:
                    
                    if i < int(self._numFrames / 2):
                    
                        rescaleSlope        = float(self._DCMs[i]
                                            [dcmRescaleSlopeAddress].value)
                        if rescaleSlope != 0:
                            rescaleSlope    = 1 / rescaleSlope


                        rescaleIntercept    = float(self._DCMs[i]
                                            [dcmRescaleInterceptAddress].value)
                            
                        rescaleSlopes.append(rescaleSlope)
                        rescaleIntercepts.append(rescaleIntercept)
                        
                    else:
                        
                        rescaleSlopes.append([])  
                        rescaleIntercepts.append([])
                        
                except:
                #If no rescale values can be found, the values can be 
                #calculated as such: 
                #Set the rescale slope and intersect to go from -venc to 
                #venc. Only if the frame is velocity or phase.
                
                #Note: This assumes that the values in the frame do 
                #actually range from -venc to venc. If this is not the 
                #case, the calculated velocities might be off slightly.
                
                #TODO: find the min and max possible raw values and not just
                #the ones that occur. Look into how many bits are used to store
                #data per voxel.
                #16 bits -> 4096?
                
                    if i < int(self._numFrames / 2):
                    
                            venc    = self._tags['venc'] 
                            minVal  = np.min(self._rawFrames[i])
                            maxVal  = np.max(self._rawFrames[i])
                            
                            slope   = (maxVal - minVal) / ( 2 * venc) 
                            intercept   = (maxVal - minVal) / 2 + minVal
                            
                            rescaleSlopes.append(slope)
                            rescaleIntercepts.append(intercept)
                    
                    else:
                        
                        rescaleSlopes.append([])  
                        rescaleIntercepts.append([])

            
            

        self._tags['rescaleSlopes']     = rescaleSlopes
        self._tags['rescaleIntercepts'] = rescaleIntercepts



    def _findVEncoding(self):
        """Gets the velocity encoding maximum in the z-direction from the DCM.
        It's assumed that this is constant for all frames."""
       
        #First try default location:
        address1    = 0x0018, 0x9197
        address2    = 0x0018, 0x9217
        
        venc    = None
        
        try:
            venc    = self._DCMs[0][address1][address2].value
            
        except:
            #Try other frames
            for frameNo in range(1,self._numFrames):
                try:
                    venc    = self._DCMs[frameNo][address1][address2].value
                except:
                    pass
        
        if venc is not None:
            
            #Adjust for units
            if self._checkVencUnit():
                venc /= 10
            
            self._tags['venc'] = venc
            return
        
        
        
        #Next try the private locations
        
        #Philips        
        if 'philips' in self._tags['manufacturer']:
            vencAddress                 = 0x2001, 0x101A
            
            #If private location does not work default to intercept value
            try:
                venc                        = self._DCMs[0][vencAddress].value
                venc                        = venc[-1] 
            except:
            #Try other frames
                vencFrames = np.zeros(np.size(range(0,self._numFrames)))
                for frameNo in range(0,self._numFrames):
                    
                    address1                 = 0x0040, 0x9096
                    address2                 = 0x0040, 0x9224
                    vencFrames[frameNo]      = -1*self._DCMs[frameNo][address1][0][address2].value
                    
                venc = max(vencFrames) #NOT FOOLPROOF YET!!
        #GE
        if 'ge' in self._tags['manufacturer']:
            vencAddress                 = 0x0019, 0x10CC
            venc                        = self._DCMs[0][vencAddress].value
            
            if type(venc) == 'list':
                venc    = venc[-1]
                
            if venc > 50:
                #Change from mm/s to cm/s
                venc    /= 10
        
        
        #Siemens
        if 'siemens' in self._tags['manufacturer']:
            
            #Gather the venc from the sequence name.
            seqAddress                  = 0x0018, 0x0024
            
            for frameNo in range(self._numFrames):
                seqName                 = self._DCMs[frameNo][seqAddress].value
            
                #sequence name has the format: fl2d1_[venc]
                #Example: fl2d1_v200in
                
                #Find venc by getting the text after the underscore
                pos     = seqName.find("_v")
                if pos == -1:
                    continue
                
                vencStr = seqName[pos:]
                import re
                venc    = [int(s) for s in re.findall(r'\d+', vencStr)][0]
                

        #Adjust for units
        if self._checkVencUnit():
            venc /= 10
            
        #Write to tags        
        self._tags['venc'] = venc
            
            
            
    def _findFrameTypes(self):
        """Find the frame types per manufacturer.
        Method differs for each manifacturer."""
        
        self._tags['frameTypes'] = []
       
        #Philips
        if 'philips' in self._tags['manufacturer']:
            dcmImageTypeAddress         = 0x0008, 0x0008
            self._dcmInstanceNumber     = 0x0020, 0x0013 
            
            for i in range(self._numFrames):
                frameType = self._DCMs[i][dcmImageTypeAddress].value[2]
                self._tags['frameTypes'].append(frameType)
                
        #Siemens
        if 'siemens' in self._tags['manufacturer']:
            dcmImageTypeAddress         = 0x0008, 0x0008
            self._dcmInstanceNumber     = 0x0020, 0x0013 
            
            for i in range(self._numFrames):
                frameType = self._DCMs[i][dcmImageTypeAddress].value[2]
                self._tags['frameTypes'].append(frameType)
            
        #GE
        if 'ge' in self._tags['manufacturer']:
            self._dcmInstanceNumber     = 0x0020, 0x0013 
            #The program currently assumes the first half of a series consists
            #of phase frames and the second half of magnitude frames. 
            
            #TODO: find a way to base frametype off of dicom header.
            for i in range(self._numFrames):
                if i < int(self._numFrames/2):
                    self._tags['frameTypes'].append('Phase')
                else:
                    self._tags['frameTypes'].append('Magnitude')
            
        
        
    def _findPixelSpacing(self):
        """Find Pixel spacing in Dicom header, save it to the tags."""
        
        ps  = float(self._DCMs[0].PixelSpacing[0])
        
        self._tags['pixelSpacing'] = ps
        

    def _findNoiseScalingFactors(self):
        """Find RR intervals and TFE in Dicom header, save it to the tags"""
        
        # Philips
        if 'philips' in self._tags['manufacturer'].lower():
            
            HeartRates = np.zeros((len(self._DCMs),1))
            for i in range(self._numFrames):
                HeartRates[i] = self._DCMs[i].HeartRate
                
            RR_interval = (60 / int(self._DCMs[0].HeartRate)) * 1000
            TFE = self._DCMs[0].EchoTrainLength
            TR = self._DCMs[0][0x0018, 0x0080].value
            
            Temporal_resolution = 2*TFE*TR
            
        # Siemens
        if 'siemens' in self._tags['manufacturer'].lower():
            
            RR_intervals = np.zeros((len(self._DCMs),1))
            for i in range(self._numFrames):
                RR_intervals[i] = self._DCMs[i].NominalInterval
                
            RR_interval = np.max(RR_intervals)
            TFE = self._DCMs[0].EchoTrainLength
            TR = self._DCMs[0].RepetitionTime
            
            Temporal_resolution = TR
            
        # GE
        if 'ge' in self._tags['manufacturer'].lower():
            
            fn = "Scan_Parameters_GE.txt"
            fullpath = os.path.join(os.path.dirname(self._dcmFilenames[0]), fn)

            with open (fullpath, "r") as info:
                data=info.readlines()
                RR_interval     = data[0].replace('Heart Rate:','')
                TFE             = data[1].replace('TFE:','')
                TR              = data[2].replace('TR:','')
                
            if RR_interval == "\n":
            
                RR_intervals = np.zeros((len(self._DCMs),1))
                for i in range(self._numFrames):
                    RR_intervals[i] = self._DCMs[i].NominalInterval
                
                RR_interval = np.max(RR_intervals)
                
            else:
                
                RR_interval = (60 / int(float(RR_interval))) * 1000
                
            if TFE == "\n":
            
                TFE = self._DCMs[0].EchoTrainLength
                
            else:
                
                TFE = float(TFE)
                
            if TR == "\n":
            
                TR = self._DCMs[0].RepetitionTime
                
            else:
                
                TR = float(TR)
   
            Temporal_resolution = 2*TFE*TR
        
        self._tags['R-R Interval'] = RR_interval
        self._tags['TFE'] = TFE
        self._tags['TR'] = TR
        self._tags['Temporal resolution'] = Temporal_resolution

    def _findTargets(self):
        """
        Saves the manufacturer specific names for the phase, velocity,
        magnutide and modulus frames.
        
        """
        self._tags['targets'] = dict()
        
        #Philips
        if 'philips' in self._tags['manufacturer']:
            self._tags['targets']['phase']      = 'PHASE CONTRAST M'
            self._tags['targets']['velocity']   = 'VELOCITY MAP'
            self._tags['targets']['magnitude']  = "M_FFE"
            self._tags['targets']['modulus']    = "M_PCA"
            
        
        #Siemens
        if 'siemens' in self._tags['manufacturer']:
            self._tags['targets']['phase']      = 'P'
            self._tags['targets']['velocity']   = 'V'
            self._tags['targets']['magnitude']  = "M"
            self._tags['targets']['modulus']    = "MAG"
            
        #GE            
        if 'ge' in self._tags['manufacturer']:            
            self._tags['targets']['phase']      = 'Phase'
            self._tags['targets']['velocity']   = 'Velocity'
            self._tags['targets']['magnitude']  = "Magnitude"
            self._tags['targets']['modulus']    = "Modulus"
        
    
    def _rescaleFrames(self):
        ''' Applies the rescale slope and intercept to the frames. '''

        # import pdb; pdb.set_trace()
        
        self._rescaledFrames = []
        for i in range(len(self._rawFrames)):
            rescaleSlope        = self._tags['rescaleSlopes'][i]
            rescaleIntercept    = self._tags['rescaleIntercepts'][i]
            rawFrame            = self._rawFrames[i]
            
            #Skip the slices without slope or intercept
            if rescaleSlope == [] or rescaleIntercept == []:
                rescaledFrame   = rawFrame
            else:
                rescaledFrame   = (rawFrame - rescaleIntercept)/rescaleSlope
            
            self._rescaledFrames.append(rescaledFrame)
    
    
    # def _makeVelocityFrames(self):
    #     '''
    #     Construct velocity frames out of the phase frames if any phase frames
    #     exist. Formula: v = phase * venc / pi
    #     '''
    #     if len(self._phaseFrames) > 0:
            
    #         venc = self._tags['venc']
            
    #         #Check if the velocity frames aren't accidentally stored as phase
            
    #         if np.round(np.max(self._phaseFrames), 1) == venc and \
    #             np.round(np.min(self._phaseFrames), 1) == -venc:
               
    #             self._velocityFrames        = self._phaseFrames
    #             self._rawVelocityFrames     = self._rawPhaseFrames
    #             return
            
    #         #Else, compute velocity frames from the phaseFrames
    #         for idx in range(len(self._phaseFrames)):
    #             phaseFrame  = self._phaseFrames[idx] * venc / np.pi
    #             rawPhaseFrame  = self._rawPhaseFrames[idx] * venc / np.pi
    #             self._velocityFrames.append(phaseFrame)
    #             self._rawVelocityFrames.append(rawPhaseFrame)
            
        