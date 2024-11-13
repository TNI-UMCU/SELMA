#!/usr/bin/env python

"""
This module contains the main function of the SELMA program.

"""

# ====================================================================

import sys
from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

import SELMADataModels
import SELMAGUIModels
import SELMAGUISettings

# ====================================================================

def main():
    """ SELMA - Trial-ready Small Vessel MRI Markers """

    COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()

    app = QtWidgets.QApplication(sys.argv)


    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    app.setOrganizationName(COMPANY)
    app.setApplicationName(APPNAME)
    app.setWindowIcon(QtGui.QIcon("SELMA.png"))

    # Model classes
    SGM = SELMAGUIModels.SelmaGUIModel(APPNAME = APPNAME) #SelmaGUIModel class is getting called here
    SDM = SELMADataModels.SelmaDataModel() #SelmaDataModel class is getting called here

    # Initialise settings
    settings = SELMAGUISettings.SelmaSettings() #SelmaSettings class is getting called here
    settings.applySettings() #applySettings function is called within SelmaSettings

    # Connect signals
    # ----------------------------------------
    # Signals from mainwindow (menubar)
    # Left hand side are signals that are defined, right hand side (after .connect) are slots which are defined functions
    SGM.mainWin.loadMaskSignal      .connect(SDM.loadMaskSlot)
    SGM.mainWin.segmentMaskSignal   .connect(SDM.segmentMaskSlot)
    SGM.mainWin.openFileSignal      .connect(SDM.loadDCMSlot)
    SGM.mainWin.openClassicSignal   .connect(SDM.loadClassicDCMSlot)
    SGM.mainWin.openT1Signal        .connect(SDM.loadT1DCMSlot)
    SGM.mainWin.analyseVesselSignal .connect(SDM.analyseVesselSlot)
    SGM.mainWin.analyseBatchSignal  .connect(SDM.analyseBatchSlot)
    SGM.mainWin.switchViewSignal    .connect(SDM.switchViewSlot)
    SGM.mainWin.applyMaskSignal     .connect(SDM.applyMaskSlot)
    SGM.mainWin.saveMaskSignal      .connect(SDM.saveMaskSlot)

    # Signals from mouseEvents
    SGM.mainWin._imageViewer._scene.mouseMove.connect(SDM.pixelValueSlot)
    SGM.mainWin._imageViewer._view.wheelEventSignal.connect(SDM.newFrameSlot)

    # Signals from ImVar
    SGM.mainWin.signalObj.getVarSignal.connect(
            SDM.getVarSlot)
    SGM.mainWin.signalObj.setVarSignal.connect(
            SDM.setVarSlot)
    
    # Signals from GUI bar
    SGM.mainWin.signalObj.toggleMaskSignal.connect(SGM.toggleMaskSlot)
    SGM.mainWin.signalObj.toggleVesselSignal.connect(SGM.toggleVesselSlot)
    SGM.mainWin.signalObj.toggleVesselsSignal.connect(SGM.toggleVesselsSlot)
    SGM.mainWin.signalObj.YesButtonSignal.connect(SDM.YesButtonSlot)
    SGM.mainWin.signalObj.NoButtonSignal.connect(SDM.NoButtonSlot)
    SGM.mainWin.signalObj.repeatSelectionSignal.connect(SDM.RepeatSelectionSlot)
    SGM.mainWin.signalObj.stopSelectionSignal.connect(SDM.StopSelectionSlot)

    #Signals from settings
    SGM.mainWin.settingsWindow.thresholdSignal.connect(
        SDM.thresholdMaskSlot)

    #Signals from processing
    SDM.signalObject.sendVesselMaskSignal           .connect(SGM.setVesselMaskSlot)
    SDM.signalObject.sendSingleVesselMaskSignal     .connect(SGM.setSingleVesselMaskSlot)
    SDM.signalObject.setPixmapSignal                .connect(SGM.setPixmapSlot)
    SDM.signalObject.setProgressBarSignal           .connect(SGM.setProgressBarSlot)
    SDM.signalObject.setFrameCountSignal            .connect(SGM.setFrameCounterSlot)
    SDM.signalObject.sendMaskSignal                 .connect(SGM.setMaskSlot)
    SDM.signalObject.pixelValueSignal               .connect(SGM.mainWin._imageViewer.mouseHover)
    SDM.signalObject.errorMessageSignal             .connect(SGM.mainWin.errorMessageSlot)
    SDM.signalObject.infoMessageSignal              .connect(SGM.mainWin.infoMessageSlot)
    SDM.signalObject.manualVesselSelectionSignal    .connect(SGM.manualVesselSelectionSlot)
    SDM.signalObject.finishVesselSelectionSignal    .connect(SGM.finishVesselSelectionSlot)
    SDM.signalObject.sendImVarSignal                .connect(SGM.listenForVarsSlot)
    SDM.signalObject.setProgressLabelSignal         .connect(SGM.setProgressLabelSlot)


    # ---------------------------------------
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()