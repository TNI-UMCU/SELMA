#!/usr/bin/env python

"""
This module contains the following classes:
+ :class:`ImageViewer`

@author: Cyrano
"""

# ====================================================================

from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

import SELMAGUISettings

# ====================================================================

class BarWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(BarWidget, self).__init__()
        self._initUI()
        
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        self.settings = QtCore.QSettings(COMPANY, APPNAME)
        
        
    def _initUI(self):
        
        self.layout = QtWidgets.QVBoxLayout()
        
        self.clusterLabel   = QtWidgets.QLabel(
            "Select clustering...") # Potentially change label?
        self.clusterSelect = QtWidgets.QComboBox()
        self.clusterSelect.addItems(["Basal Ganglia",
                                     "Semioval Centre",
                                     "Advanced Clustering"])
 
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
        
        #Fill layout
        self.layout.addWidget(self.clusterLabel)        
        self.layout.addWidget(self.clusterSelect)    
        
        self.layout.addWidget(self.customClustering)    
        self.setLayout(self.layout)
        
        self.customClustering.close()
        
    def switchClustering(self):
      
        idx     = self.clusterSelect.currentIndex()
        
        if idx == 0: #Basal Ganglia
            self.settings.setValue('BasalGanglia',1)
            self.settings.setValue('SemiovalCentre',0)
            self.settings.setValue('AdvancedClustering',0)
            self.customClustering.close()
        elif idx == 1: #Semioval Centre
            self.settings.setValue('BasalGanglia',0)
            self.settings.setValue('SemiovalCentre',1)
            self.settings.setValue('AdvancedClustering',0)
            self.customClustering.close()
        elif idx == 2: #Advanced Clustering
            self.settings.setValue('BasalGanglia',0)
            self.settings.setValue('SemiovalCentre',0)
            self.settings.setValue('AdvancedClustering',1)
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
   
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        