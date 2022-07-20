#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SelmaImVar`

"""

# ====================================================================

from PyQt5 import (QtCore, QtGui, QtWidgets)
import numpy as np

# ====================================================================
class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        

class SelmaImVar(QtWidgets.QWidget):
    """
    This class contains the UI for interacting with the image variables
    loaded in the .dcm file.
    
    The settings window displays the following tabs:
        General     - for the main functioning of the program
        Ghosting    - for the removeGhosting function
        Reset       - for resetting the settings to their default
    """
    
    
    def __init__(self, signalObj):
        QtWidgets.QWidget.__init__(self)
        
        self._signalObj = signalObj
        self._changed   = False
        
        #Create window
        self._initGui()
    
    def _initGui(self):
        self.setGeometry(QtCore.QRect(100, 100, 300, 200))
        self.setWindowTitle("Image Variables")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        
        #Layout of the variables
        self.vencLabel  = QtWidgets.QLabel("Velocity Encoding (cm/s)")
        self.vencEdit   = QtWidgets.QLineEdit()
        self.vencEdit.textChanged.connect(self._variableChanged)
        self.velocityLabel = QtWidgets.QLabel("Velocity min & max")   
        self.velocityLabel.setToolTip(
            "Manually set the min and max values for the velocity frames." + 
            "The rescale slope will be calculated accordingly.")
        
        self.velocityMin = QtWidgets.QLineEdit()
        self.velocityMax = QtWidgets.QLineEdit()
        self.velocityMin.textChanged.connect(self._variableChanged)
        self.velocityMax.textChanged.connect(self._variableChanged)
        
        self.varLayout  = QtWidgets.QGridLayout()
        self.varLayout.addWidget(self.vencLabel,        0,0)
        self.varLayout.addWidget(self.vencEdit,         0,1)
        self.varLayout.addWidget(QHLine(),              1,0,2,2)
        self.varLayout.addWidget(self.velocityLabel,    2,0)
        self.varLayout.addWidget(self.velocityMin,      2,1)
        self.varLayout.addWidget(self.velocityMax,      2,2)
        
        #Layout of the buttons
        self.okButton       = QtWidgets.QPushButton("OK")
        self.cancelButton   = QtWidgets.QPushButton("Cancel")
        self.okButton.pressed.connect(self._okButtonPressed)
        self.cancelButton.pressed.connect(self.close)
        
        self.buttonLayout   = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        
        #Window layout
        self.errorLabel     = QtWidgets.QLabel("")
        self.errorLabel.setStyleSheet("QLabel {color: red }")
        
        self.layout         = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.varLayout)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.errorLabel)
        
        self.setLayout(self.layout)
    
    ## Public
    
        
    @QtCore.pyqtSlot(dict)
    def listenForVars(self, variables):
        """Extract the variables from the dictionary that was sent and store 
        them in the window."""
        
        venc    = variables["venc"]
        if venc is not None:
            self.vencEdit.setText(str(venc))
        
        minres, maxres  = variables["velscale"]
        if minres is not None and maxres is not None:
            self.velocityMin.setText(str(np.round(minres,5)))
            self.velocityMax.setText(str(np.round(maxres,5)))
        
        
    def focus(self):
        """
        Gets called whenever the window is activated.
        """
        self._getVariables()
        self._changed   = False
        
        
    ###### Private
    
    def _okButtonPressed(self):
        """
        Collects all the values from the window, stores them in a dictionary 
        and sends them to the SelmaData class to be managed there.
        
        """
        
        if not self._changed:
            self.close()
            return
        
        #The dictionary
        res             = dict()
        
        #All the variables
        #venc
        venc            = self.vencEdit.text()
        if venc is not None:
            try:
                venc        = float(venc)
            except:
                self.errorLabel.setText(
                        "Velocity Encoding has to be a number")
                return        
            if venc == 0:
                self.errorLabel.setText(
                        "Velocity Encoding cannot be 0")
                return
            res["venc"]     = venc


        #velocitymin & max
        velmin          = self.velocityMin.text()
        velmax          = self.velocityMax.text()
        
        if velmin is not None and velmax is not None:
            try:
                velmin      = float(velmin)
            except:
                self.errorLabel.setText(
                        "Velocity Minimum has to be a number")
                return
            
            #velocitymax
            
            try:
                velmax      = float(velmax)
            except:
                self.errorLabel.setText(
                        "Velocity maximum has to be a number")
                return
        
            if velmin >= velmax:
                self.errorLabel.setText(
                    "Velocity maximum has to be bigger than velocity minimum")
                return
                
            res["velscale"]   = [velmin, velmax]
        
        # other variables...
        
        
        #Send variables to DataModels        
        self._signalObj.setVarSignal.emit(res)
        self.close()
        
    def _variableChanged(self):
        """
        Keeps track of any changes to the variables
        """
        self._changed = True
        
        
    def _getVariables(self):
        """
        Gets the necessary variables from the program.
        """
        self._signalObj.getVarSignal.emit()

# ====================================================================