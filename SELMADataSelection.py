# -*- coding: utf-8 -*-
"""
This fucntion belongs to the SELMAData module. 


@author: spham2
"""

import numpy as np
import SELMAData
import SELMADataIO


class SELMADataSelection:
    
    def VesselSelection(self):
        
        self.mask = np.zeros(self._mask.shape,
                            dtype = np.int32)
        
        if self._clusters == []:
            
            return
    
        self.mask += self._clusters[self.VesselCounter]
        
        self._singleVesselMask        = self.mask.astype(bool)
            
        self._signalObject.sendSingleVesselMaskSignal.emit(self._singleVesselMask)
            
        self._signalObject.manualVesselSelectionSignal.emit(self._axes_ratio[self.VesselCounter],
                                                                self._mask,
                                                                self._singleVesselMask,
                                                                self._vesselMask,
                                                          "Please select if you want to keep or discard this vessel")
        
    def FinishSelection(self):
    
        self._included_vessels = []
        self._excluded_vessels = []
        
        for cluster_idx in self._Included_Vessels:
            
            
            
            self._included_vessels.append(self._clusters[cluster_idx])
            
        for cluster_idx in self._Excluded_Vessels:
            
            self._excluded_vessels.append(self._clusters[cluster_idx])
            
        mask = np.zeros(self._mask.shape, dtype = np.int32)
        
        for labels in self._included_vessels:
            mask += labels
        
        self._IncludedVesselMask        = mask.astype(bool)
        
        mask = np.zeros(self._mask.shape, dtype = np.int32)
        
        for labels in self._excluded_vessels:
            mask += labels
        
        self._ExcludedVesselMask        = mask.astype(bool)
        
        #Send included vessels back to the GUI for final selection
        self._signalObject.sendVesselMaskSignal.emit(self._IncludedVesselMask)
        
        SELMADataIO._saveVesselMask(self, self._IncludedVesselMask)
        
        #Send excluded vessels back to the GUI for final selection (single vessel signal is repurposed for this)
        self._signalObject.sendSingleVesselMaskSignal.emit(self._ExcludedVesselMask)
        
        #Send signal back to GUI to notify user that vessel selection has finished
        self._signalObject.finishVesselSelectionSignal.emit(len(self._included_vessels),
                                                            len(self._excluded_vessels))
        
        
        
        
