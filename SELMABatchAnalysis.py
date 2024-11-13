# -*- coding: utf-8 -*-
"""
Created on Tue Jul  6 15:10:14 2021

@author: spham2
"""

import os
import numpy as np
from PyQt5 import (QtCore)

import SELMAData
import SELMADataIO
import SELMADataModels
import threading

def EnhancedBatchAnalysis(dirName, files, self):
    
    self._BatchAnalysisFlag = True

    #Make list of all suitable .dcm files
    dcms = []
    for file in files:
        if file.find(".dcm") != -1 and file.find("mask") == -1:
            dcms.append(file)
  
    i       = 0 
    total   = len(dcms)
    
    if not dcms:
    
        self.signalObject.errorMessageSignal.emit(
             "No DICOM files found in folder. This batch job will "+
             "be stopped.")
        
        return

    batchAnalysisResults = dict()
    
    #Iterate over all suitable .dcm files.
    for dcm in dcms:

        self.signalObject.setProgressLabelSignal.emit(
                "Patient %.0f out of %.0f" %(i + 1, total))
        
        self._SDO   = SELMAData.SELMADataObject(self.signalObject,
                                                dcmFilename = dirName 
                                                + '/' + dcm,
                                                classic = False)
        
        name        = dcm[:-4]
        #find mask

        for file in files:
            if file.find(name) != -1 and file.find("mask") != -1:
                if file[-4:] == ".dcm" or file[-4:] == ".npy":
                    #Now it will find the dcm object itself.
#                        self._SDO.setT1(file)
#                        break
                    pass
                else:
                    
                    try:
                        
                        mask = SELMADataIO.loadMask(dirName + '/' + 
                                                    file)
                                                
                        self._SDO.setMask(mask)
                        
                    except:
                    
                        self.signalObject.errorMessageSignal.emit(
            "The mask of %s has a version of .mat file that " %(dcm) +
            "is not supported. Please save it as a non-v7.3 file "+
            "and try again. Moving on to next scan.")
                        
                        #return

                        break
        
        #If no mask is found, move on to the next image
        if self._SDO.getMask() is None:
            
            self.signalObject.infoMessageSignal.emit(
             "Mask of %s not found in folder. Moving to next scan"
             %(dcm))
            
            continue
        
        #Do vessel analysis
        
        self._SDO.analyseVessels(self._BatchAnalysisFlag)
  
        #Save results
        #TODO: support for other output types.
        vesselDict, velocityDict = self._SDO.getVesselDict()
                        
        if not bool(vesselDict):
            
            continue
  
        #Save in single file
        #batchAnalysisResults[i] = self._SDO.getBatchAnalysisResults()
        batchAnalysisResults[i] = SELMADataIO.getBatchAnalysisResults(self._SDO)
        
        outputName = dirName + '/batchAnalysisResults.mat' 
        SELMADataIO.writeBatchAnalysisDict(batchAnalysisResults, 
                                           outputName)
              
        #Emit progress to progressbar
        self.signalObject.setProgressBarSignal.emit(int(100 * i / 
                                                        total))
            
        i += 1
    
    outputName = dirName + '/batchAnalysisResults.mat' 
    SELMADataIO.writeBatchAnalysisDict(batchAnalysisResults, 
                                       outputName)
    
    #Emit progress to progressbar
    self.signalObject.setProgressBarSignal.emit(int(100))
    self.signalObject.setProgressLabelSignal.emit(
                "Batch analysis complete!"
                )
  
def ClassicBatchAnalysis(dirName, files, self):
    
    self._BatchAnalysisFlag = True
    
    i       = 0 
    total   = len(files)
    
    batchAnalysisResults = dict()
    
    for subject in files:
        
        if not os.path.isdir(dirName + '/' + subject):
            
            continue
        
        subject_folder = os.listdir(dirName + '/' + subject)
        
        dcmFilename = []
        
        for file in subject_folder:
            
            if file.endswith('.mat'):
                
                if file.find('mask') != -1:
                    
                    try:
                        
                        mask = SELMADataIO.loadMask(dirName + '/' + 
                                                    subject + '/' + 
                                                    file)
    
                    except:
                    
                        self.signalObject.errorMessageSignal.emit(
            "The mask of %s has a version of .mat file that " 
            %(subject) + "is not supported. Please save it as a " + 
            "non-v7.3 file and try again. Moving on to next scan.")
                        
                        #return
    
                        break
                
                continue
            
            elif file.endswith('.log'):
                
                continue
            
            # elif file.endswith('.dcm'): # In case of Marseille data
                
            #     continue
            
            elif file.endswith('.npy'):
                
                continue
            
            elif file.endswith('.xml'):
                
                continue
            
            elif file.endswith('.txt'):
                
                continue
            
            # Skip DICOMDIR files
            elif os.path.getsize(dirName + '/' + subject + '/' 
                                 + file) < 100000:
                
                continue
            
            else:
    
                dcmFilename.append(dirName + '/' + subject + '/' + file)
            
        if dcmFilename == []:
            
            continue
        
        self.signalObject.setProgressLabelSignal.emit(
                "Patient %.0f out of %.0f" %(i + 1, total))
        
        self._SDO   = SELMAData.SELMADataObject(self.signalObject,
                                                dcmFilename ,
                                                classic = True)
        
        self._SDO.setMask(mask)
                                 
        #If no mask is found, move on to the next image
        if self._SDO.getMask() is None:
            
            self.signalObject.infoMessageSignal.emit(
             "Mask of %s not found in folder. Moving to next subject"
             %(subject))
            
            continue
        
        #Do vessel analysis

        self._SDO.analyseVessels(self._BatchAnalysisFlag)
      
        #Save results
        #TODO: support for other output types.
        vesselDict, velocityDict = self._SDO.getVesselDict()
        
        if not bool(vesselDict):
            
            continue
    
        #Save in single file
        #batchAnalysisResults[i] = self._SDO.getBatchAnalysisResults()
        batchAnalysisResults[i] = SELMADataIO.getBatchAnalysisResults(self._SDO)
        
        outputName = dirName + '/batchAnalysisResults.mat' 
        SELMADataIO.writeBatchAnalysisDict(batchAnalysisResults, 
                                           outputName)
              
        #Emit progress to progressbar
        self.signalObject.setProgressBarSignal.emit(int(100 * i 
                                                        / total))
            
        i += 1
        
    outputName = dirName + '/batchAnalysisResults.mat' 
    SELMADataIO.writeBatchAnalysisDict(batchAnalysisResults, 
                                       outputName)
    
    #Emit progress to progressbar
    self.signalObject.setProgressBarSignal.emit(int(100))
    self.signalObject.setProgressLabelSignal.emit(
                "Batch analysis complete!"
                )    