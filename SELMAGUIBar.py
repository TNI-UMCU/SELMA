#!/usr/bin/env python

"""
This module contains the following classes:
+ :class:`ImageViewer`

@author: Cyrano
"""

# ====================================================================

import numpy as np
from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

import SELMAGUISettings
import SELMAGUI
import SELMADataSelection

# ====================================================================
        
class BarWidget(QtWidgets.QWidget):
    
    def __init__(self, signalObj):
        super(BarWidget, self).__init__()
        
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        self.settings = QtCore.QSettings(COMPANY, APPNAME)

        self.signalObj = signalObj
        self._initUI()
        
    def _initUI(self):
        
        self.layout = QtWidgets.QVBoxLayout()
        
        self.clusterLabel   = QtWidgets.QLabel(
            "Select clustering...") # Potentially change label?
        self.clusterSelect = QtWidgets.QComboBox()
        self.clusterSelect.addItems([" ",
                                     "Basal Ganglia",
                                     "Semioval Centre",
                                     "Middle Cerebral Artery",
                                     "Advanced Clustering"])
        
        # Initialise GUI bar settings
        
        self.settings.setValue('BasalGanglia',          'false')
        self.settings.setValue('SemiovalCentre',        'false')
        self.settings.setValue('MiddleCerebralArtery',  'false')
        self.settings.setValue('AdvancedClustering',    'false')
        
        self.settings.setValue('PositiveMagnitude',     'false') 
        self.settings.setValue('NegativeMagnitude',     'false') 
        self.settings.setValue('IsointenseMagnitude',   'false') 
        self.settings.setValue('PositiveFlow',          'false') 
        self.settings.setValue('NegativeFlow',          'false')
 
        self.clusterSelect.activated.connect(self.switchClustering)

        #Create hidden custom clustering tool
        self.customClustering   = QtWidgets.QWidget()
        ccLayout                = QtWidgets.QGridLayout()
        
        posMagLab   = QtWidgets.QLabel("Pos. Mag.")
        negMagLab   = QtWidgets.QLabel("Neg. Mag.")
        isoMagLab   = QtWidgets.QLabel("Iso. Mag.")
        
        posMagBox   = QtWidgets.QCheckBox()
        posMagBox.stateChanged.connect(self.customMagChanged)
        posMagBox.setObjectName("pos")
        negMagBox   = QtWidgets.QCheckBox()
        negMagBox.stateChanged.connect(self.customMagChanged)
        negMagBox.setObjectName("neg")
        isoMagBox   = QtWidgets.QCheckBox()
        isoMagBox.stateChanged.connect(self.customMagChanged)
        isoMagBox.setObjectName("iso")
        
        posVelLab   = QtWidgets.QLabel("Pos. vel.")
        negVelLab   = QtWidgets.QLabel("Neg. vel.")
        
        posVelBox   = QtWidgets.QCheckBox()
        posVelBox.stateChanged.connect(self.customVelChanged)
        posVelBox.setObjectName("pos")
        negVelBox   = QtWidgets.QCheckBox()
        negVelBox.stateChanged.connect(self.customVelChanged)
        negVelBox.setObjectName("neg")
        
        ccLayout.addWidget(posMagLab, 0, 0)
        ccLayout.addWidget(negMagLab, 1, 0)
        ccLayout.addWidget(isoMagLab, 2, 0)
        
        ccLayout.addWidget(posMagBox, 0, 1)
        ccLayout.addWidget(negMagBox, 1, 1)
        ccLayout.addWidget(isoMagBox, 2, 1)
        
        ccLayout.addWidget(posVelLab, 4, 0)
        ccLayout.addWidget(negVelLab, 5, 0)
        
        ccLayout.addWidget(posVelBox, 4, 1)
        ccLayout.addWidget(negVelBox, 5, 1)
        
        self.customClustering.setLayout(ccLayout) 
        
        #Create vessel selection layout
        self.vesselSelection   = QtWidgets.QWidget()
        selectionLayout        = QtWidgets.QGridLayout()
        
        toggleMaskLab          = QtWidgets.QLabel("Toggle mask")
        toggleMaskBox          = QtWidgets.QCheckBox()
        toggleMaskBox.stateChanged.connect(self.toggleMask)
        toggleMaskBox.setObjectName("togMask")
        
        toggleVesselLab          = QtWidgets.QLabel("Toggle vessel")
        toggleVesselBox          = QtWidgets.QCheckBox()
        toggleVesselBox.stateChanged.connect(self.toggleVessel)
        toggleVesselBox.setObjectName("togVess")
        
        selectionLab           = QtWidgets.QLabel("Include vessel?")
        selectionYesButton     = QtWidgets.QPushButton("Yes")
        selectionNoButton      = QtWidgets.QPushButton("No")
        selectionYesButton.pressed.connect(self.YesButtonPushed)
        selectionNoButton.pressed.connect(self.NoButtonPushed)
        
        selectionLayout.addWidget(toggleMaskLab, 0, 0)
        selectionLayout.addWidget(toggleMaskBox, 0, 1)
        selectionLayout.addWidget(toggleVesselLab, 1, 0)
        selectionLayout.addWidget(toggleVesselBox, 1, 1)
        selectionLayout.addWidget(selectionLab, 2, 0)
        selectionLayout.addWidget(selectionYesButton, 2, 1)
        selectionLayout.addWidget(selectionNoButton, 2, 2)
   
        self.vesselSelection.setLayout(selectionLayout)
        
        #Create final layout
        self.finalSelection   = QtWidgets.QWidget()
        finalselectionLayout  = QtWidgets.QGridLayout()
        
        toggleMaskLab          = QtWidgets.QLabel("Toggle mask")
        toggleMaskBox          = QtWidgets.QCheckBox()
        toggleMaskBox.stateChanged.connect(self.toggleMask)
        toggleMaskBox.setObjectName("togMask")
        
        toggleVesselsLab          = QtWidgets.QLabel("Toggle vessels")
        toggleVesselsBox          = QtWidgets.QCheckBox()
        toggleVesselsBox.stateChanged.connect(self.toggleVessels)
        toggleVesselsBox.setObjectName("togVessels")
        
        repeatSelectionLab          = QtWidgets.QLabel("Repeat vessel selection?")
        repeatSelectionYesButton     = QtWidgets.QPushButton("Yes")
        repeatSelectionNoButton      = QtWidgets.QPushButton("No")
        repeatSelectionYesButton.pressed.connect(self.repeatSelectionYesButtonPushed)
        repeatSelectionNoButton.pressed.connect(self.repeatSelectionNoButtonPushed)
        
        finalselectionLayout.addWidget(toggleMaskLab, 0, 0)
        finalselectionLayout.addWidget(toggleMaskBox, 0, 1)
        finalselectionLayout.addWidget(toggleVesselsLab, 1, 0)
        finalselectionLayout.addWidget(toggleVesselsBox, 1, 1)
        finalselectionLayout.addWidget(repeatSelectionLab, 2, 0)
        finalselectionLayout.addWidget(repeatSelectionYesButton, 2, 1)
        finalselectionLayout.addWidget(repeatSelectionNoButton, 2, 2)
        
        self.finalSelection.setLayout(finalselectionLayout)
        
        #Fill layout
        self.layout.addWidget(self.clusterLabel)  
        self.layout.addWidget(self.vesselSelection) 
        self.layout.addWidget(self.finalSelection) 
        self.layout.addWidget(self.clusterSelect)    
        self.layout.addWidget(self.customClustering)    
         
        self.setLayout(self.layout)
        self.vesselSelection.close()
        self.finalSelection.close()
        self.customClustering.close()
        
    def switchClustering(self):
      
        idx     = self.clusterSelect.currentIndex()
        
        if idx == 0: # No clustering selected
            self.settings.setValue('BasalGanglia',          'false')
            self.settings.setValue('SemiovalCentre',        'false')
            self.settings.setValue('MiddleCerebralArtery',  'false')
            self.settings.setValue('AdvancedClustering',    'false')
        
            self.settings.setValue('PositiveMagnitude',     'false') 
            self.settings.setValue('NegativeMagnitude',     'false') 
            self.settings.setValue('IsointenseMagnitude',   'false') 
            self.settings.setValue('PositiveFlow',          'false') 
            self.settings.setValue('NegativeFlow',          'false')
 
        
        elif idx == 1: #Basal Ganglia
            self.settings.setValue('BasalGanglia',          'true')
            self.settings.setValue('SemiovalCentre',        'false')
            self.settings.setValue('MiddleCerebralArtery',  'false')
            self.settings.setValue('AdvancedClustering',    'false')
            
            self.settings.setValue('PositiveMagnitude',     'true') 
            self.settings.setValue('NegativeMagnitude',     'false') 
            self.settings.setValue('IsointenseMagnitude',   'false') 
            self.settings.setValue('PositiveFlow',          'true') 
            self.settings.setValue('NegativeFlow',          'false')
            
            self.customClustering.close()
        elif idx == 2: #Semioval Centre
            self.settings.setValue('BasalGanglia',          'false')
            self.settings.setValue('SemiovalCentre',        'true')
            self.settings.setValue('MiddleCerebralArtery',  'false')
            self.settings.setValue('AdvancedClustering',    'false')
            
            self.settings.setValue('PositiveMagnitude',     'true') 
            self.settings.setValue('NegativeMagnitude',     'true') 
            self.settings.setValue('IsointenseMagnitude',   'true') 
            self.settings.setValue('PositiveFlow',          'false') 
            self.settings.setValue('NegativeFlow',          'true')
            
            self.customClustering.close()
        elif idx == 3: #Middle Cerebral Artery
            self.settings.setValue('BasalGanglia',          'false')
            self.settings.setValue('SemiovalCentre',        'false')
            self.settings.setValue('MiddleCerebralArtery',  'true')
            self.settings.setValue('AdvancedClustering',    'false')
            
            self.settings.setValue('PositiveMagnitude',     'true') 
            self.settings.setValue('NegativeMagnitude',     'true') 
            self.settings.setValue('IsointenseMagnitude',   'true') 
            self.settings.setValue('PositiveFlow',          'false') 
            self.settings.setValue('NegativeFlow',          'true')
            
            self.customClustering.close()
        elif idx == 4: #Advanced Clustering
            self.settings.setValue('BasalGanglia',          'false')
            self.settings.setValue('SemiovalCentre',        'false')
            self.settings.setValue('MiddleCerebralArtery',  'false')
            self.settings.setValue('AdvancedClustering',    'true')
            self.customClustering.show()
        elif self.customClustering.isVisible():
            self.customClustering.close()
        
            
        
    def customMagChanged(self, state):
        sender = self.sender()
        
        if sender.objectName() == "pos":
           self.settings.setValue('PositiveMagnitude', state == 2) 
        elif sender.objectName() == "neg":
           self.settings.setValue('NegativeMagnitude', state == 2) 
        elif sender.objectName() == "iso":
           self.settings.setValue('IsointenseMagnitude', state == 2) 
           
       

    def customVelChanged(self, state):
        sender = self.sender()
        
        if sender.objectName() == "pos":
           self.settings.setValue('PositiveFlow', state == 2) 
        elif sender.objectName() == "neg":
           self.settings.setValue('NegativeFlow', state == 2) 
        
#Setters:
    
    def manualVesselSelection(self, axes_ratio, mask, single_vessel, vessels_mask, string):
        
        # self.layout = QtWidgets.QVBoxLayout()
        
        # self.Label   = QtWidgets.QLabel("The axes ratio is "
        #                                        + str(axes_ratio) +". " + string) 
        
        # self.layout.addWidget(self.Label)        

        # self.setLayout(self.layout)
        
        self._single_vessel = single_vessel
        
        self._vessels_mask = vessels_mask
        
        self._mask = mask
        
        self.layout = QtWidgets.QVBoxLayout()
        
        self.clusterLabel.setText("The currently selected vessel is marked in red.\n\nThe axes ratio is "
                                               + str(axes_ratio) +".\n" + string) 
        
       
        self.vesselSelection.show()
        
    def finalVesselSelection(self, amount_included, amount_excluded):
        
        self.clusterLabel.setText("Manual vessel selection has been completed.\n\n"+ str(amount_included) + " vessels (blue) have been included.\n"+ str(amount_excluded) + " vessels (red) have been excluded.") 
        self.vesselSelection.close()
        self.finalSelection.show()

    def toggleMask(self, state):

        if state == 2:
            
            self.signalObj.toggleMaskSignal.emit(self._mask, state)
            
        elif state == 0:
            
            self.signalObj.toggleMaskSignal.emit(self._mask, state)
            
    def toggleVessel(self, state):

        if state == 2:
            
            self.signalObj.toggleVesselSignal.emit(self._single_vessel, self._vessels_mask, state)
            
        elif state == 0:
            
            self.signalObj.toggleVesselSignal.emit(self._single_vessel, self._vessels_mask, state)
    
    def toggleVessels(self, state):

        if state == 2:
            
            self.signalObj.toggleVesselsSignal.emit(self._vessels_mask, state)
            
        elif state == 0:
            
            self.signalObj.toggleVesselsSignal.emit(self._vessels_mask, state)    
    
    def YesButtonPushed(self):
        
        self.signalObj.YesButtonSignal.emit(1)
        
    def NoButtonPushed(self):
        
        self.signalObj.NoButtonSignal.emit(1)
        
    def repeatSelectionYesButtonPushed(self):
        
        self.signalObj.repeatSelectionSignal.emit(0)

        self._vessels_mask = []
        self._single_vessel = []
        
        self.finalSelection.close()
        
    def repeatSelectionNoButtonPushed(self):
        
        self.signalObj.stopSelectionSignal.emit(0)
        self.finalSelection.close()
        
        
        
        
        
        
        
        
        
        
        
        
        