#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SELMAMainWindow`
+ :class:`SGMSignals`
"""

# ====================================================================

import numpy as np
from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

import SELMAImageViewer
import SELMAGUISettings
import SELMAGUIImVar

# ====================================================================


class SGMSignals(QtCore.QObject):
    """
    This class inherits from a QObject in order to store and connect
    pyqtSignals. It's used to send new signals to any subwindows that might
    have been opened from the GUI.
    
    """
    
    #ImVar Signals
    getVarSignal        = QtCore.pyqtSignal()
    setVarSignal        = QtCore.pyqtSignal(dict)


class SELMAMainWindow(QtWidgets.QMainWindow):
    """  """

    def __init__(self):
        """:param QPixmap pixmap: |QPixmap| to display"""
        super(SELMAMainWindow, self).__init__()

        self._imageViewer = SELMAImageViewer.ImageViewer()
        self.setCentralWidget(self._imageViewer)

        self.createActions()
        self.createMenus()
        self.settingsWindow = SELMAGUISettings.SelmaSettings()
        
        self.statusBar().showMessage('SELMA')
        
        #Subwindows:
        self.signalObj      = SGMSignals()
        self._imVarWindow    = SELMAGUIImVar.SelmaImVar(self.signalObj)
        
        #filenames
        self._fname         = None
        
     
    '''Public'''
    # ------------------------------------------------------------------

    #Signals
    
    loadMaskSignal = QtCore.pyqtSignal(str)
    """ Load Mask **Signal**.
    Emitted when the user triggers the loadMaskAction.    
    """
    
    segmentMaskSignal = QtCore.pyqtSignal(list)
    """ Segment Mask **Signal**.
    Emitted when the user triggers the loadMaskAction.    
    """
    
    saveMaskSignal = QtCore.pyqtSignal(str)
    """ Signals that the drawn ROIs should be saved to the disk."""
    
    applyMaskSignal = QtCore.pyqtSignal(np.ndarray)
    """ Signals that the drawn ROIs should be made into a mask
    for use in the analysis."""
    
    openFileSignal = QtCore.pyqtSignal(str)
    """ Open File **Signal**.
    Emitted when the user triggers the openAct.    
    """
    
    openClassicSignal = QtCore.pyqtSignal(list)
    """ Open Directory **Signal**.
    Emitted when the user triggers the openClassicAct.    
    """
    
    openT1Signal = QtCore.pyqtSignal(str)
    """ Open T1 File **Signal**.
    Emitted when the user triggers the openT1Act.    
    """
    
    analyseVesselSignal = QtCore.pyqtSignal()
    """ Analyse Vessels **Signal**.
    Emitted when the user triggers the analyseVesselAct.    
    """
    
    analyseBatchSignal = QtCore.pyqtSignal(str)
    """ Analyse Batch **Signal**.
    Emitted when the user triggers the analyseBatchAct.    
    """
    
    switchViewSignal = QtCore.pyqtSignal()
    """ Switch View **Signal**
    Emitted when the user triggers the switchViewAct
    """
    
    #Setters
    
    def setMask(self, mask):
        """Passes along the mask to the imageViewer."""
        self._imageViewer.setMask(mask)
        
    def setPixmap(self, pixmap):
        """Passes along the pixmap to the imageViewer."""
        self._imageViewer.setPixmap(pixmap)
    
    def setVesselMask(self, mask):
        """Passes along the vessel mask to the imageViewer."""
        self._imageViewer.setVesselMask(mask)
    
    def setFrameCounter(self, frameCounter, maxFrames):
        """Passes along the frame count to the imageViewer."""
        self._imageViewer.setFrameCounter(frameCounter, maxFrames)
    
    '''Private'''
    # ------------------------------------------------------------------

    def createActions(self):
        """Create actions for the menus."""

        #File Actions
        self.exitAct = QtWidgets.QAction(
            "E&xit", self,
            shortcut=QtGui.QKeySequence.Quit,
            statusTip="Exit the application",
            triggered=QtWidgets.qApp.closeAllWindows)
        
        self.openAct = QtWidgets.QAction(
            "O&pen Dicom", self,
            shortcut=QtGui.QKeySequence.Open,
            statusTip="Open PCA Dicom (Ctrl+O)",
            triggered=self._openFile)
        
        self.openClassicAct = QtWidgets.QAction(
            "O&pen Classic Dicom", self,
            shortcut="Ctrl+Shift+O",
            statusTip="Open Directory (Ctrl+Shift+O)",
            triggered=self._openClassic)
        
        self.openT1Act  = QtWidgets.QAction(
            "O&pen T1 image", self,
            shortcut="Ctrl+Alt+O",
            statusTip="Open T1 Dicom (Ctrl+Alt+O)",
            triggered=self._openT1)
        
        
        #Mask Actions
        self.loadMaskAct  = QtWidgets.QAction(
            "&Load Mask", self,
            statusTip="Load an existing mask from a file.",
            triggered=self._loadMask)

#        self.applyMaskAct  = QtWidgets.QAction(
#            "&Apply Mask", self,
#            statusTip="Apply the drawn mask.",
#            triggered=self._applyMask)
        
        self.segmentMaskAct  = QtWidgets.QAction(
            "&Segment Mask", self,
            statusTip="Segments a white matter mask from the image.",
            triggered=self._segmentMask)
        
        self.clearMaskAct  = QtWidgets.QAction(
            "&Clear Mask", self,
            statusTip="clears all masks from the image.",
            triggered=self._clearMask)
        
        self.saveMaskAct    = QtWidgets.QAction(
            "&Save Mask", self,
            statusTip= "Saves the current mask to the disk.",
            triggered=self._saveMask)

        #Analyse Actions
        
        self.analyseVesselsAct =  QtWidgets.QAction(
            "&Analyse Vessels", self,
            statusTip="Analyse the vessels in the image.",
            triggered=self._analyseVessels)
        
        self.analyseBatchAct =  QtWidgets.QAction(
            "&Analyse Batch", self,
            statusTip="Perform vessel analysis on all files in a directory.",
            triggered=self._analyseBatch)
        
        
        #View Actions
        
        self.switchViewAct = QtWidgets.QAction(
            "&Switch View", self,
            statusTip="Switch view between PCA and T1 image",
            shortcut= "Tab",
            triggered=self._switchView)
        
        #scroll actions
        self.scrollToTopAct = QtWidgets.QAction(
            "&Top", self,
            shortcut=QtGui.QKeySequence.MoveToStartOfDocument,
            triggered=self._imageViewer.scrollToTop)

        self.scrollToBottomAct = QtWidgets.QAction(
            "&Bottom", self,
            shortcut=QtGui.QKeySequence.MoveToEndOfDocument,
            triggered=self._imageViewer.scrollToBottom)

        self.scrollToBeginAct = QtWidgets.QAction(
            "&Left Edge", self,
            shortcut=QtGui.QKeySequence.MoveToStartOfLine,
            triggered=self._imageViewer.scrollToBegin)

        self.scrollToEndAct = QtWidgets.QAction(
            "&Right Edge", self,
            shortcut=QtGui.QKeySequence.MoveToEndOfLine,
            triggered=self._imageViewer.scrollToEnd)

        self.centerView = QtWidgets.QAction(
            "&Center", self,
            shortcut="5",
            triggered=self._imageViewer.centerView)

        #zoom actions
        self.zoomInAct = QtWidgets.QAction(
            "Zoo&m In (25%)", self,
            shortcut=QtGui.QKeySequence.ZoomIn,
            triggered=self._imageViewer.zoomIn)

        self.zoomOutAct = QtWidgets.QAction(
            "Zoom &Out (25%)", self,
            shortcut=QtGui.QKeySequence.ZoomOut,
            triggered=self._imageViewer.zoomOut)

        self.actualSizeAct = QtWidgets.QAction(
            "Actual &Size", self,
            shortcut="/",
            triggered=self._imageViewer.actualSize)

        self.fitToWindowAct = QtWidgets.QAction(
            "Fit &Image", self,
            shortcut="*",
            triggered=self._imageViewer.fitToWindow)

        self.fitWidthAct = QtWidgets.QAction(
            "Fit &Width", self,
            shortcut="Alt+Right",
            triggered=self._imageViewer.fitWidth)

        self.fitHeightAct = QtWidgets.QAction(
            "Fit &Height", self,
            shortcut="Alt+Down",
            triggered=self._imageViewer.fitHeight)
        
        #settings actions
        self.settingsAct = QtWidgets.QAction(
            "Open &Settings", self,
            triggered = self._openSettings)
        
        self.imageVariablesAct = QtWidgets.QAction(
            "Image Variables", self,
            triggered = self._imageVariables)

    def createMenus(self):
        """Create the menus."""

        #Create File Menu
        self.fileMenu = QtWidgets.QMenu("&File")
        self.fileMenu.addAction(self.exitAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.openClassicAct)
        self.fileMenu.addAction(self.openT1Act)
        
        #Create Mask Menu
        self.maskMenu = QtWidgets.QMenu("&Mask")
        self.maskMenu.addAction(self.loadMaskAct)
#        self.maskMenu.addAction(self.applyMaskAct)
        self.maskMenu.addAction(self.segmentMaskAct)
        self.maskMenu.addAction(self.clearMaskAct)
        self.maskMenu.addAction(self.saveMaskAct)
        
        #Create Analyse Menu
        self.analyseMenu = QtWidgets.QMenu("&Analyse")
        self.analyseMenu.addAction(self.analyseVesselsAct)
        self.analyseMenu.addAction(self.analyseBatchAct)        

        #Create view Menu
        self.viewMenu = QtWidgets.QMenu("&View", self)
        self.viewMenu.addAction(self.switchViewAct)

        #Create Scroll Menu
        self.scrollMenu = QtWidgets.QMenu("&Scroll", self)
        self.scrollMenu.addAction(self.scrollToTopAct)
        self.scrollMenu.addAction(self.scrollToBottomAct)
        self.scrollMenu.addAction(self.scrollToBeginAct)
        self.scrollMenu.addAction(self.scrollToEndAct)
        self.scrollMenu.addAction(self.centerView)

        #Create Zoom Menu
        self.zoomMenu = QtWidgets.QMenu("&Zoom", self)
        self.zoomMenu.addAction(self.zoomInAct)
        self.zoomMenu.addAction(self.zoomOutAct)
        self.zoomMenu.addSeparator()
        self.zoomMenu.addAction(self.actualSizeAct)
        self.zoomMenu.addAction(self.fitToWindowAct)
        self.zoomMenu.addAction(self.fitWidthAct)
        self.zoomMenu.addAction(self.fitHeightAct)
        
        #create Settings Menu
        self.settingsMenu = QtWidgets.QMenu("&Settings", self)
        self.settingsMenu.addAction(self.settingsAct)
        self.settingsMenu.addAction(self.imageVariablesAct)

        #Add menus to menubar
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.maskMenu)
        self.menuBar().addMenu(self.analyseMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.scrollMenu)
        self.menuBar().addMenu(self.zoomMenu)
        self.menuBar().addMenu(self.settingsMenu)
        

    #Public slots
    # ------------------------------------------------------------------
    
    @QtCore.pyqtSlot(str)
    def errorMessageSlot(self, message):
        """Creates an error dialog with the input message."""
        self._error_dialog = QtWidgets.QMessageBox.critical(self,
                                                            "Error",
                                                            message)
        
    def infoMessageSlot(self, message):
        """Creates an error dialog with the input message."""
        self._info_dialog = QtWidgets.QMessageBox.information(self,
                                                              "Information",
                                                              message)

    def setProgressBar(self, val):
        """Updates the progressbar of the imageViewer."""
        self._imageViewer.setProgressBar(val)

    
    def setProgressLabel(self, text):
        """Updates the statusBar with text from elsewhere in the program."""
#        self._imageViewer.setProgressLabel(text)
        self.statusBar().showMessage(text)


    def passOnVars(self, variables):
        self._imVarWindow.listenForVars(variables)
    
    #Private slots
    # ------------------------------------------------------------------
    
    @QtCore.pyqtSlot()
    def _openFile(self):
        """Triggered when the open action is called."""
        
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Open Dicom',
                                                      '',
                                                      'Dicom (*.dcm)')
        if len(fname) != 0:
            self._fname     = fname
            self.openFileSignal.emit(fname)
        
    @QtCore.pyqtSlot()
    def _openClassic(self):
        """Triggered when the open classic action is called."""
        
        
        
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fnames, _ = dialog.getOpenFileNames(self,
                                           "Open classic Dicom files")
        
        if len(fnames) != 0:
            self.openClassicSignal.emit(fnames)
            
            
    @QtCore.pyqtSlot()
    def _openT1(self):
        """Triggered when the open T1 action is called."""
         
        
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Open T1 Dicom',
                                                      '',
                                                      'Dicom (*.dcm)')
        
        if len(fname) != 0:
            self.openT1Signal.emit(fname)
        
    #Mask Menu
    @QtCore.pyqtSlot()
    def _loadMask(self):
        """Triggered when the load Mask action is called."""
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Open mask',
                                                      '',
                                                      '(*.npy *.png *.mat)')
        if len(fname) != 0:
            self.loadMaskSignal.emit(fname)
        
    
        
    @QtCore.pyqtSlot()
    def _segmentMask(self):
        """Triggered when the segment Mask action is called."""
        libs    = self.getLibraries()                
        self.segmentMaskSignal.emit(libs)

    @QtCore.pyqtSlot()
    def _clearMask(self):
        """Triggered when the clear Mask action is called."""
        self._imageViewer._scene.resetMask()



    @QtCore.pyqtSlot()
    def _saveMask(self):
        """Triggered when the saveMask action is called."""
        
        #First, write the current mask to the Dataobject.
        mask = self._imageViewer._scene.getMask()
        
        if mask is None:
            self.errorMessageSlot("No mask loaded")
            return
        
        self.applyMaskSignal.emit(mask)
        
        if self._fname is not None:
            maskFname   = self._fname[:-4] + "-mask"
        else:
            maskFname   = None
        
        #Next, get the filename to save the mask to.
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                      'Save Mask',
                                                      maskFname,
                                                      '(*.npy *.png *.mat)')
        if len(fname) != 0:
            self.saveMaskSignal.emit(fname)
    
    #Analyse Menu
    @QtCore.pyqtSlot()
    def _analyseVessels(self):
        """Triggered when the  analyse Vessels action is called.
        Sends the current mask to the data models, then sends the  
        analyseVessel signal.
        """
        
        mask = self._imageViewer._scene.getMask()
        if mask is None:
            self.errorMessageSlot("No mask loaded")
            return
        
        self.applyMaskSignal.emit(mask)
        
        self.analyseVesselSignal.emit()
        
    
    @QtCore.pyqtSlot()
    def _analyseBatch(self):
        """Triggered when the analyse batch action is called."""
         
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                      'Open folder',
                                                      ''
                                                      )
        if len(dirname) != 0:
            self.analyseBatchSignal.emit(dirname)
            
    @QtCore.pyqtSlot()
    def _switchView(self):
        self.switchViewSignal.emit()
        
    @QtCore.pyqtSlot()
    def _openSettings(self):
        self.settingsWindow.show()
        
    
    @QtCore.pyqtSlot()
    def _imageVariables(self):
        self._imVarWindow.show()
        self._imVarWindow.focus()
        
    
    # ------------------------------------------------------------------

    #overriden events

    def keyPressEvent(self, keyEvent):
        """Overrides to enable panning while dragging.

        :param QKeyEvent keyEvent: instance of |QKeyEvent|"""
        assert isinstance(keyEvent, QtGui.QKeyEvent)
        if keyEvent.key() == QtCore.Qt.Key_Space:
            if (not keyEvent.isAutoRepeat() and
                not self._imageViewer.handDragging):
                self._imageViewer.enableHandDrag(True)
            keyEvent.accept()
        else:
            keyEvent.ignore()
            super(SELMAMainWindow, self).keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent):
        """Overrides to disable panning while dragging.

        :param QKeyEvent keyEvent: instance of |QKeyEvent|"""
        assert isinstance(keyEvent, QtGui.QKeyEvent)
        if keyEvent.key() == QtCore.Qt.Key_Space:
            if not keyEvent.isAutoRepeat() and self._imageViewer.handDragging:
                self._imageViewer.enableHandDrag(False)
            keyEvent.accept()
        else:
            keyEvent.ignore()
            super(SELMAMainWindow, self).keyReleaseEvent(keyEvent)

    def closeEvent(self, event):
        """Overrides close event to save application settings.

        :param QEvent event: instance of |QEvent|"""
        self.writeSettings()
        event.accept()

    # ------------------------------------------------------------------

    def writeSettings(self):
        """Write application settings."""
        settings = QtCore.QSettings()
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())
        settings.setValue('windowgeometry', self.saveGeometry())
        settings.setValue('windowstate', self.saveState())

    def readSettings(self):
        """Read application settings."""
        settings = QtCore.QSettings()
        pos = settings.value('pos', QtCore.QPoint(200, 200))
        size = settings.value('size', QtCore.QSize(400, 400))
        self.move(pos)
        self.resize(size)
        if settings.contains('windowgeometry'):
            self.restoreGeometry(settings.value('windowgeometry'))
        if settings.contains('windowstate'):
            self.restoreState(settings.value('windowstate'))
            
            
    def getLibraries(self):
        """
            Checks for the existence of necessary libraries, prompts the user if
            none exist. 
            
            returns
                A list with all the libraries
        """
    
        COMPANY, APPNAME, _ = SELMAGUISettings.getInfo()
        settings = QtCore.QSettings(COMPANY, APPNAME)
        
        libs    = []
        
        #SPM
        try:
            dirname     = settings.value("spmDir")
            if dirname  is None:
                raise Exception
        except:
            dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                            self,
                                                            'Open SPM12 folder',
                                                            ''
                                                            )
            settings.setValue("spmDir",      dirname)
            
        libs.append(dirname)
            
        try:
            dirname     = settings.value("dcm2niiDir")
            if dirname  is None:
                raise Exception
        except:
            dirname = QtWidgets.QFileDialog.getExistingDirectory(
                                                            self,
                                                            'Open dcm2nii folder',
                                                            ''
                                                            )
            settings.setValue("dcm2niiDir",      dirname)
        
        libs.append(dirname)
        
        return libs