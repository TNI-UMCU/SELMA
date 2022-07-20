# -*- coding: utf-8 -*-
"""
This fucntion belongs to the SELMAData module. Calculation of the velocity 
trace, average velocity and normalised pulsatility index takes place in this 
function for every vessel.

@author: spham2
"""

import numpy as np
import SELMAGUISettings
from PyQt5 import QtCore

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
    
def obtainFilters(self):
    
    if self._readFromSettings('AdvancedClustering'):
        
        PositiveMagnitude = self._readFromSettings('PositiveMagnitude')
        NegativeMagnitude = self._readFromSettings('NegativeMagnitude')
        IsointenseMagnitude = self._readFromSettings('IsointenseMagnitude')
        
        PositiveFlow = self._readFromSettings('PositiveFlow')
        NegativeFlow = self._readFromSettings('NegativeFlow')
        
        self._Magnitude_filter = np.array([PositiveMagnitude, NegativeMagnitude, 
                                     IsointenseMagnitude])
        self._Flow_filter = np.array([PositiveFlow, NegativeFlow])
    
    meanVelocity    = np.mean(self._correctedVelocityFrames,axis = 0)
    
    self._V_cardiac_cycle = np.zeros((len(self._lone_vessels),
                                self._correctedVelocityFrames.shape[0] 
                                + 3))

    self._Magnitudes = np.zeros((len(self._lone_vessels),3))
    self._Flows = np.zeros((len(self._lone_vessels),2))

    for idx, vessel in enumerate(self._lone_vessels):
    
        vesselCoords   = np.nonzero(vessel)

        vessel_velocities = abs(meanVelocity[vesselCoords[0],
                                             vesselCoords[1]])
            
        pidx = np.where(vessel_velocities == max(vessel_velocities))
         
        self._V_cardiac_cycle[idx,0] = vesselCoords[0][pidx[0][0]]
        self._V_cardiac_cycle[idx,1] = vesselCoords[1][pidx[0][0]]
        
        self._Flows[idx,0] = round(self._sigFlowPos[vesselCoords[0][pidx[0][0]],
                            vesselCoords[1][pidx[0][0]]],  4)
        self._Flows[idx,1] = round(self._sigFlowNeg[vesselCoords[0][pidx[0][0]],
                            vesselCoords[1][pidx[0][0]]],  4)
        self._Magnitudes[idx,0] = round(self._sigMagPos[vesselCoords[0]
                            [pidx[0][0]],vesselCoords[1][pidx[0][0]]],  4)
        self._Magnitudes[idx,1] = round(self._sigMagNeg[vesselCoords[0]
                            [pidx[0][0]],vesselCoords[1][pidx[0][0]]],  4)
        self._Magnitudes[idx,2] = round(self._sigMagIso[vesselCoords[0]
                            [pidx[0][0]],vesselCoords[1][pidx[0][0]]],  4)
        
        self._V_cardiac_cycle[idx,2] = idx + 1
        
        self._V_cardiac_cycle[
        idx,3:self._V_cardiac_cycle.shape[1]] = self._correctedVelocityFrames[
        :,vesselCoords[0][pidx[0][0]],vesselCoords[1][pidx[0][0]]].ravel()
    
def filterVelocities(self):
      
    if self._readFromSettings('BasalGanglia'):
                        
        self._V_cardiac_cycle = self._V_cardiac_cycle[np.intersect1d(
        np.where(self._Flows[:,0] == 1)[0],
        np.where(self._Magnitudes[:,0] == 1)[0]),:]
    
        self._included_vessels = [i for j, 
        i in enumerate(self._lone_vessels) 
        if j in np.intersect1d(np.where(self._Flows[:,0] == 1)[0]
                               ,np.where(self._Magnitudes[:,0] == 1)[0])]

    elif self._readFromSettings('SemiovalCentre'):
 
        self._V_cardiac_cycle = self._V_cardiac_cycle[np.where(self._Flows[
            :,1]  == 1)[0],:]
    
        self._included_vessels = [i for j, 
        i in enumerate(self._lone_vessels) if j in np.where(self._Flows[:,1] 
                                                            == 1)[0]]
        
    elif self._readFromSettings('AdvancedClustering'):
    
        selectedMagnitudes = np.where(self._Magnitude_filter == 1)[0]
        selectedFlows = np.where(self._Flow_filter == 1)[0]
        
        self._V_cardiac_cycle = self._V_cardiac_cycle[np.intersect1d(
            np.where(self._Flows[:,selectedFlows] == 1)[0], np.where(
                self._Magnitudes[:,selectedMagnitudes] == 1)[0]),:]
        
        self._included_vessels = [i for j, 
        i in enumerate(self._lone_vessels) 
        if j in np.intersect1d(np.where(self._Flows[:,selectedFlows] == 1)[0],
                    np.where(self._Magnitudes[:,selectedMagnitudes] == 1)[0])]

def calculateParameters(self):
    """
    Computes the average velocity over all the detected vessels and 
    computes the PI over all the vessels using the average normalised
    velocity. This implementation completely corresponds with the method2
    found in MATLAB.
    """
  
    obtainFilters(self)
    filterVelocities(self)

    for idx in np.where(self._V_cardiac_cycle[:,3:
                self._correctedVelocityFrames.shape[0] + 3] > 
                        self._selmaDicom.getTags()['venc'])[0]:
 
        del(self._included_vessels[idx])

    V_cardiac_cycle = abs(self._V_cardiac_cycle)
    
    V_cardiac_cycle = np.delete(V_cardiac_cycle, np.where(
    V_cardiac_cycle[:,3:self._correctedVelocityFrames.shape[0] + 3] 
    > self._selmaDicom.getTags()['venc'])[0], 0)
                
    VmeanPerVesselList = np.zeros((V_cardiac_cycle.shape[0],1))
    MeanCurveOverAllVessels = np.zeros((1,self._correctedVelocityFrames.
                                        shape[0]))
    
    NormMeanCurvePerVessel = np.zeros((V_cardiac_cycle.shape[0],
                            self._correctedVelocityFrames.shape[0]))
    normMeanCurveOverAllVessels = np.zeros((1,
                                self._correctedVelocityFrames.shape[0]))

    for i in range(0,V_cardiac_cycle.shape[0]):
        
       VmeanPerVesselList[i,0:V_cardiac_cycle.shape[0]] = np.mean(
           V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]])
       
       MeanCurveOverAllVessels = MeanCurveOverAllVessels + np.squeeze((
           V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]]/
           (V_cardiac_cycle.shape[0])))
       
       NormMeanCurvePerVessel[i,0:self._correctedVelocityFrames.
        shape[0]] = V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]]/np.mean(
            V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]])
       
       # Velocity curves are first normalised and then averaged
       normMeanCurveOverAllVessels = (normMeanCurveOverAllVessels + 
        V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]]/np.mean(
        V_cardiac_cycle[i,3:V_cardiac_cycle.shape[1]])/
        (V_cardiac_cycle.shape[0]))
         
    # Compute mean velocity  
    self._Vmean = np.mean(MeanCurveOverAllVessels)
    
    # Compute PI using normalised velocity curve of cardiac cycle averaged 
    # over all vessels
    self._PI_norm = (np.max(normMeanCurveOverAllVessels) - np.min(
        normMeanCurveOverAllVessels))/np.mean(normMeanCurveOverAllVessels)
    
    # Compute standard error of the mean of Vmean (adapted from MATLAB)
    allstdV = np.std(VmeanPerVesselList,ddof = 1)
    self._allsemV = allstdV/np.sqrt(V_cardiac_cycle.shape[0])
    
    # Compute standard error of the mean of PI_norm (adapted from MATLAB)
    allimaxV = np.where(normMeanCurveOverAllVessels == np.max(
        normMeanCurveOverAllVessels))[1]
    alliminV = np.where(normMeanCurveOverAllVessels == np.min(
        normMeanCurveOverAllVessels))[1]
    allstdnormV = np.std(NormMeanCurvePerVessel,ddof = 1,axis = 0)
    allstdmaxV = allstdnormV[allimaxV];
    allstdminV = allstdnormV[alliminV];
    allsemmaxV = allstdmaxV/np.sqrt(V_cardiac_cycle.shape[0])
    allsemminV = allstdminV/np.sqrt(V_cardiac_cycle.shape[0])
    allcovarmaxminV = 0
    self._allsemPI = np.sqrt(allsemmaxV**2 + allsemminV**2 - 2*
                             allcovarmaxminV)[0]