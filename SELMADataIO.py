#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SELMADataIO`

"""


# ====================================================================

import numpy as np

# ====================================================================
#IO

import pydicom
import imageio
import scipy.io
import time
# import h5py
from PyQt5 import (QtCore, QtGui, QtWidgets)
# ====================================================================

import SELMAGUISettings

# ====================================================================

"""
This module contains all methods concerning IO.
"""

"PUBLIC"

def getBatchAnalysisResults(self):
    
    _makeBatchAnalysisDict(self)
    
    return self._batchAnalysisDict
    

def loadMask( fname):
    """Loads a mask file. The following types are supported:
        .png
        .npy
        .mat
        
    Args:
        fname(str): path to the mask file.
        
    Returns:
        numpy.ndarray containing the binary mask. 
    """
    
    #find extension
    ext = fname[-4:]
    
    if      ext == ".png":
        mask = imageio.imread(fname)
    elif    ext == ".npy":
        mask = np.load(fname)
    elif    ext == ".mat":
        
        try:

            #Non-h5 file
            maskDict    = scipy.io.loadmat(fname)
            maskKey     = list(maskDict.keys())[-1]
            mask        = maskDict[maskKey]
            
            
        except:
            # #H5 file, used for matlab v7.3 and higher
            # H5py currently doesn' work anymore, unsure why. 
            # User will be prompted to resave.
            # arrays = {}
            # f = h5py.File(fname, 'r')
            # for key, value in f.items():
            #     arrays[key] = np.array(value)
                
            # mask = arrays[key]
            # mask = np.swapaxes(mask, 0,1)
            return None
        
    return mask


def saveMask(fname, mask):
    """Saves a mask file. The following types are supported:
        .png
        .npy
        
    Args:
        fname(str): path to where the mask is saved.
        mask(numpy.ndarray): the mask to be saved.
    """

    #find extension
    ext         = fname[-4:]
  
    if      ext == ".png":
        mask = mask.astype(np.uint8)
        imageio.imwrite(fname, mask)
    elif    ext == ".npy":
        np.save(fname, mask)
        scipy.io.savemat(fname[0:len(fname)-4], {'WMslice': mask})
        
        #Workaround for Linux systems
    else:
        np.save(fname, mask)
        scipy.io.savemat(fname, {'WMslice': mask})
        
def _saveVesselMask(self, vessel_mask):
    """Saves a vessel mask file in case of manual vessel selection. 

    """
    
    fname = self._dcmFilename[:-4]
    fname += "-Vessel_Mask.npy"

    np.save(fname, vessel_mask)
    scipy.io.savemat(fname[0:len(fname)-4], {'Vessel_mask': vessel_mask})

    
def _makeBatchAnalysisDict(self):
    """"Makes a dictionary containing the following statistics per scan:
        No. of vessels
        V_mean
        V_mean SEM
        PI_mean
        PI_mean SEM
        mean Velocity Trace
    """
    
    self._batchAnalysisDict = dict()
    
    # if self._readFromSettings('deduplicate'):

    self._batchAnalysisDict['No_of_vessels'] = self._velocityDict[0][
                                                    'No. included vessels'] 
    self._batchAnalysisDict['V_mean'] = self._velocityDict[0][
                                                    'Vmean vessels'] 
    self._batchAnalysisDict['PI_mean'] = self._velocityDict[0][
                                                    'PI_norm vessels']
    self._batchAnalysisDict['PI_median'] = self._velocityDict[0][
                                                    'median PI_norm vessels']
    
    if not self._readFromSettings('MiddleCerebralArtery'):
            
        self._batchAnalysisDict['V_mean_SEM'] = self._velocityDict[0][
                                                        'Vmean SEM'] 
        self._batchAnalysisDict['PI_mean_SEM'] = self._velocityDict[0][
                                                        'PI_norm SEM']  
        self._batchAnalysisDict['PI_mdiean_SEM'] = self._velocityDict[0][
                                                        'median PI_norm SEM'] 
        
    self._batchAnalysisDict['Filename'] = self._dcmFilename   

    velocityTrace = np.zeros((self._batchAnalysisDict['No_of_vessels'],
                              len(self._correctedVelocityFrames)))
            
    for blob in range(1, self._batchAnalysisDict['No_of_vessels'] + 1):
        
        for vessel in range(0,len(self._vesselDict)):
            
            if self._vesselDict[vessel]['iblob'] == blob and (
                    self._vesselDict[vessel]['ipixel'] == 1):

                for num in range(1,len(self._correctedVelocityFrames) + 1):
                   
                   if num < 10:
                           
                       numStr = '0' + str(num)
                           
                   else:
                           
                       numStr = str(num)
                       
                   velocityTrace[blob - 1,num - 1] = abs(self._vesselDict[
                                                  vessel]['Vpha' + numStr])
                
                break

    self._batchAnalysisDict['Velocity_trace'] = np.mean(velocityTrace,
                                                        axis=0)

def _writeToFile(self):
    """
    Creates a filename for the output and passes it to writeVesselDict
    along with the vesselDict object to be written. The velocityDict 
    object is written to a different file. 
    """
    
    #TODO: Add scan name to error message of no vessels found
    #Message if no vessels were found
    if len(np.nonzero(self._clusters)[0]) == 0:
        
        self._signalObject.errorMessageSignal.emit("No vessels Found")
        return
    
    #Get filename for textfile output for vesselData
    fname = self._dcmFilename[:-4]
    fname += "-Vessel_Data.txt"
    
    #Get filename for textfile output for velocityData
    fname_vel = self._dcmFilename[:-4]
    fname_vel += "-averagePIandVelocity_Data.txt"
    
    addonDict = getAddonDict(self)
    
    writeVesselDict(self._vesselDict,
                                addonDict,
                                fname)
    
    writeVelocityDict(self._velocityDict,
                                addonDict,
                                fname_vel)
    
def getAddonDict(self):
    """Makes a dictionary that contains the necessary information for
    repeating the analysis.""" 
    
    COMPANY, APPNAME, version = SELMAGUISettings.getInfo()
    COMPANY             = COMPANY.split()[0]
    APPNAME             = APPNAME.split()[0]
    version             = version.split()[0]
    settings            = QtCore.QSettings(COMPANY, APPNAME)
    
    addonDict   = dict()
    
    for key in settings.allKeys():
        addonDict[key]  = settings.value(key)
 
    venc                = self._selmaDicom.getTags()['venc']
    addonDict['venc']   = venc
    addonDict['version']= version
    
    date                = time.localtime()
    datestr     = str(date[2]) + '/' + str(date[1]) + '/' + str(date[0])
    timestr     = str(date[3]) + ':' + str(date[4]) + ':' + str(date[5])
    addonDict['date']   = datestr
    addonDict['time']   = timestr
    
    addonDict['filename'] = self._dcmFilename
    
    return addonDict        
    

def writeVesselDict(vesselDict, addonDict, fname):
    """
    Writes the vesselDict object to a .txt file.
    
    Args:
        vesselDict(dict): dictionary containing all the analysis values
        of all the significant vessels in the analysed dicom.
        
        fname(str): path to where the dictionary needs to be saved.
    
    """
    
    #Find if the decimalComma setting is turned on
    COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
    COMPANY             = COMPANY.split()[0]
    APPNAME             = APPNAME.split()[0]
    settings            = QtCore.QSettings(COMPANY, APPNAME)
    decimalComma        = settings.value('decimalComma') == 'true'
    
    with open(fname, 'w') as f:    
        #Write headers
        for key in vesselDict[0].keys():
            f.write(key)
            f.write('\t')
        f.write('\n')
    
        #Write vesseldata
        for i in range(len(vesselDict))    :
            for key in vesselDict[0].keys():
                text    = str(vesselDict[i][key])
                if decimalComma:
                    text    = text.replace('.',',')
                f.write(text)
                f.write('\t')
            f.write('\n')
            
        #Write additional info
        f.write('\n')
        for key in addonDict.keys():
            f.write(key)
            f.write('\t')
            f.write(str(addonDict[key]))
            f.write('\n')
            
def writeVelocityDict(velocityDict, addonDict, fname):
    """
    Writes the velocityDict object to a .txt file. This is a separate text file
    from the vesselDict object
    
    Args:
        velocityDict(dict): dictionary containing all the average velocities
        of all the significant vessels in the analysed dicom.
        
        fname(str): path to where the dictionary needs to be saved.
    
    """
    
    #Find if the decimalComma setting is turned on
    COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
    COMPANY             = COMPANY.split()[0]
    APPNAME             = APPNAME.split()[0]
    settings            = QtCore.QSettings(COMPANY, APPNAME)
    decimalComma        = settings.value('decimalComma') == 'true'
    
    with open(fname, 'w') as f:    
    
        for key in velocityDict[0].keys():
            f.write(key)
            f.write('\t')
            text    = str(velocityDict[0][key])
            if decimalComma:
                text    = text.replace('.',',')
            f.write(text)
            f.write('\n')
            
        #Write additional info
        f.write('\n')
        for key in addonDict.keys():
            f.write(key)
            f.write('\t')
            f.write(str(addonDict[key]))
            f.write('\n')
            
def writeBatchAnalysisDict(batchAnalysisResults, fname):
    """
    Writes the batchAnalysisResults object to a .mat file. This is a struct
    object that contains the data of all scans in a dataset
    
    Args:
        velocityDict(dict): dictionary containing all the average velocities
        of all the significant vessels in the analysed dicom.
        
        fname(str): path to where the dictionary needs to be saved.
    
    """
    
    struct_object = []
    
    for scan in range(0, len(batchAnalysisResults)):
          
        struct_object.append(batchAnalysisResults[scan])        
    
    scipy.io.savemat(fname,{'Results':[struct_object]})



