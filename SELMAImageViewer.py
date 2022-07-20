#!/usr/bin/env python

"""
This module contains the following classes:
+ :class:`ImageViewer`

@author: Cyrano
"""

# ====================================================================

import numpy as np
from PyQt5 import (QtCore, QtGui, QtWidgets)
import qimage2ndarray

# ====================================================================

import SELMAGraphicsScene
import SELMAGraphicsView
import SELMAGUIBar

# ====================================================================

class ImageViewer(QtWidgets.QFrame):
    """Image Viewer than can pan & zoom images (|QPixmap|\ s)."""

    def __init__(self):
        super(ImageViewer, self).__init__()
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)

        self._relativeScale = 1.0 #scale relative to other ImageViewer instances
        self._zoomFactorDelta = 1.25
        
        #Initial pixmap 
        self._pixmapItem = QtWidgets.QGraphicsPixmapItem()
        
        #GraphicsScene - handles displaying the pixmap, and masks.
        self._scene = SELMAGraphicsScene.GraphicsScene(self._pixmapItem,
                                                       self)
        #Connect signals
        self._scene.updateProgressBar.connect(self.setProgressBar)
        self._scene.adjustContrastSignal.connect(self.adjustDisplay)
        
        #GraphicsView - handles the zooming and resizing.
        self._view = SELMAGraphicsView.SynchableGraphicsView(self._scene)
        self._view.setInteractive(True)
        self._view.setViewportUpdateMode(
                QtWidgets.QGraphicsView.MinimalViewportUpdate)
        self._view.setTransformationAnchor(
                QtWidgets.QGraphicsView.AnchorViewCenter)
        self._view.wheelNotches.connect(self.handleWheelNotches)
       


        self._initUI()
        
    def _initUI(self):
        
        
        #Create background
        self._scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))
        self._view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        #Initial label if any
        # self._label = QtWidgets.QLabel()
        # #self._label.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        # self._label.setFrameStyle(QtWidgets.QFrame.Panel)
        # self._label.setAutoFillBackground(True);
        # self._label.setBackgroundRole(QtGui.QPalette.ToolTipBase)
#        self.viewName = name

        #Labels 
        self.valueLabel         = SELMAGraphicsView.ValueHoverLabel()
        self.frameCountLabel    = QtWidgets.QLabel()
        #Progressbar & message
        self.bar                = QtWidgets.QProgressBar()
        progressLayout          = QtWidgets.QVBoxLayout()
        progressLayout.addWidget(self.bar)
        
        #Create bottom layout
        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addWidget(self.valueLabel)
        bottomLayout.addLayout(progressLayout)
        bottomLayout.addWidget(self.frameCountLabel)
        
        #Create layout which holds view
        viewLayout = QtWidgets.QVBoxLayout()
        # viewLayout.setContentsMargins(0, 0, 0, 0)
        #layout.setSpacing(0)
        viewLayout.addWidget(self._view)
        viewLayout.addLayout(bottomLayout)
        
        #Create layout which holds right hand side bar
        self.barWidget  = SELMAGUIBar.BarWidget()
        barLayout       = QtWidgets.QHBoxLayout()
        barLayout.addLayout(viewLayout)
        barLayout.addWidget(self.barWidget)
        
        self.setLayout(barLayout)

        self.enableScrollBars(True)
        self._view.show()

    # ------------------------------------------------------------------
    '''Public'''
    
    #Properties
    # ------------------------------------------------------------------

    @property
    def pixmap(self):
        """The currently viewed |QPixmap| (*QPixmap*)."""
        return self._pixmapItem.pixmap()

    @property
    def viewName(self):
        """The name associated with ImageViewer (*str*)."""
        return self._name
    
    @property
    def handDragging(self):
        """Hand dragging state (*bool*)"""
        return self._view.handDragging

    @property
    def scrollState(self):
        """Tuple of percentage of scene extents
        *(sceneWidthPercent, sceneHeightPercent)*"""
        return self._view.scrollState

    @property
    def zoomFactor(self):
        """Zoom scale factor (*float*)."""
        return self._view.zoomFactor

    @property
    def _horizontalScrollBar(self):
        """Get the ImageViewer horizontal scrollbar widget (*QScrollBar*).

        (Only used for debugging purposes)"""
        return self._view.horizontalScrollBar()

    @property
    def _verticalScrollBar(self):
        """Get the ImageViewer vertical scrollbar widget (*QScrollBar*).

        (Only used for debugging purposes)"""
        return self._view.verticalScrollBar()

    @property
    def _sceneRect(self):
        """Get the ImageViewer sceneRect (*QRectF*).

        (Only used for debugging purposes)"""
        return self._view.sceneRect()
    
    
    
    #Setters
    # ------------------------------------------------------------------
    
    def setPixmap(self, array):
        """Changes the original pixmap. """
        self._originalPixmap = array
        
        qimage = qimage2ndarray.array2qimage(array, normalize = True)
        pixmap = QtGui.QPixmap(qimage)
        
        #Add the pixmap to the scene
        self._pixmapItem.setPixmap(pixmap)
        self._pixmapItem.setOffset(-pixmap.width()  / 2.0,
                                   -pixmap.height() / 2.0)
        self._pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self._pixmapItem.setZValue(0)
        
        self._pixmapItem.setPixmap(pixmap)
        self.fitToWindow()
        
        #Update the scene
        self._scene.resetContrast()
        self._scene.setActive(True)
        
#        self._scene.setPixmap(self._pixmapItem)

    
    def setMask(self, mask):
        """Applies a new mask to the |QGraphicsScene| (*QGraphicsScene*)."""
        self._scene.setMask(mask)
        
    def setVesselMask(self, mask):
        """Applies a new vessel mask to the 
        |QGraphicsScene| (*QGraphicsScene*)."""
        self._scene.setVesselMask(mask)
        
    def setFrameCounter(self, frameCounter, maxFrames):
        """Updates the |QLabel| (*QLabel*) that stores the frame count. """
        string = str(frameCounter) + " / " + str(maxFrames)
        self.frameCountLabel.setText(string)
    
#    @pixmap.setter
#    def pixmap(self, pixmap):
#        """Sets a new |QPixmap| (*QPixmap*)."""
#        assert isinstance(pixmap, QtGui.QPixmap)
#        self._pixmapItem.setPixmap(pixmap)
#        self._pixmapItem.setOffset(-pixmap.width()/2.0, -pixmap.height()/2.0)
#        self._pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
#        self.fitToWindow()
    
    # @viewName.setter
    # def viewName(self, name):
    #     """Sets a new name associated with ImageViewer (*str*)."""
    #     if name:
    #         self._label.setText("<b>%s</b>" % name)
    #         self._label.show()
    #     else:
    #         self._label.setText("")
    #         self._label.hide()
    #     self._name = name
        
    @scrollState.setter
    def scrollState(self, state):
        """Sets a new scrollstate. 
        *(sceneWidthPercent, sceneHeightPercent)*"""
        self._view.scrollState = state
        
    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        """Sets a new zoom scale factor (*float*)."""
        if newZoomFactor < 1.0:
            self._pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        else:
            self._pixmapItem.setTransformationMode(QtCore.Qt.FastTransformation)
        self._view.zoomFactor = newZoomFactor
    

        
    
    #Public Slots
    # ------------------------------------------------------------------
    
    @QtCore.pyqtSlot(int)
    def setProgressBar(self, val):
        """ Updates the progressbar to the given value. """
        self.bar.setValue(val)

#    def setProgressLabel(self, text):
#        """ Updates the Progresslabel with the specified message."""
#        self.progressLabel.setText(text)
        
    '''Private'''

    #Private Slots
    # ------------------------------------------------------------------

    @QtCore.pyqtSlot()
    def scrollToTop(self):
        """Scroll to top of image."""
        self._view.scrollToTop()

    @QtCore.pyqtSlot()
    def scrollToBottom(self):
        """Scroll to bottom of image."""
        self._view.scrollToBottom()

    @QtCore.pyqtSlot()
    def scrollToBegin(self):
        """Scroll to left side of image."""
        self._view.scrollToBegin()

    @QtCore.pyqtSlot()
    def scrollToEnd(self):
        """Scroll to right side of image."""
        self._view.scrollToEnd()

    @QtCore.pyqtSlot()
    def centerView(self):
        """Center image in view."""
        self._view.centerView()

    @QtCore.pyqtSlot(bool)
    def enableScrollBars(self, enable):
        """Set visiblility of the view's scrollbars.

        :param bool enable: True to enable the scrollbars """
        self._view.enableScrollBars(enable)

    @QtCore.pyqtSlot(bool)
    def enableHandDrag(self, enable):
        """Set whether dragging the view with the hand cursor is allowed.

        :param bool enable: True to enable hand dragging """
        self._view.enableHandDrag(enable)

    @QtCore.pyqtSlot()
    def zoomIn(self):
        """Zoom in on image."""
        self.scaleImage(self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        """Zoom out on image."""
        self.scaleImage(1 / self._zoomFactorDelta)

    @QtCore.pyqtSlot()
    def actualSize(self):
        """Change zoom to show image at actual size.

        (image pixel is equal to screen pixel)"""
        self.scaleImage(1.0, combine=False)

    @QtCore.pyqtSlot()
    def fitToWindow(self):
        """Fit image within view."""
        if not self._pixmapItem.pixmap():
            return
        self._pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self._view.fitInView(self._pixmapItem, QtCore.Qt.KeepAspectRatio)
#        self._view.checkTransformChanged()

    @QtCore.pyqtSlot()
    def fitWidth(self):
        """Fit image width to view width."""
        if not self._pixmapItem.pixmap():
            return
        margin = 2
        viewRect = self._view.viewport().rect().adjusted(margin, margin,
                                                         -margin, -margin)
        factor = viewRect.width() / self._pixmapItem.pixmap().width()
        self.scaleImage(factor, combine=False)

    @QtCore.pyqtSlot()
    def fitHeight(self):
        """Fit image height to view height."""
        if not self._pixmapItem.pixmap():
            return
        margin = 2
        viewRect = self._view.viewport().rect().adjusted(margin, margin,
                                                         -margin, -margin)
        factor = viewRect.height() / self._pixmapItem.pixmap().height()
        self.scaleImage(factor, combine=False)



    #Display contrast & threshold settings
    # ------------------------------------------------------------------
    
    def adjustDisplay(self, contrastFactor, brightness):
        """Adjusts the display pixmap by the defined brightness 
        and contrast.
        
        
        The pixmap doesn't seem to be normalised between 0 and 255 correctly.
        This leads to the image being very bright once it's adjusted and 
        truncated in the code below. 
        Properly normalising the image causes the adjustment of contrast and 
        brightness to malfunction. Therefore the bug is left in. 
        """
        
        #Begin with the original
        displayPixmap   = np.copy(self._originalPixmap)

        #Change the contrast
        C               = contrastFactor
        F               = (259*(C + 255) / (255*(259 - C)))
        
        displayPixmap   = F * (displayPixmap - 128) + 128
        
        #Change the brightness
        displayPixmap   += brightness
        
        #Truncate the values
        displayPixmap[displayPixmap < 0]    = 0
        displayPixmap[displayPixmap > 255]  = 255
        
        #Change the pixmap on the screen
        self.displayPixmap = displayPixmap
        self.updateDisplay()
        
        
    def updateDisplay(self):
        """Draws the updated display on the screen."""
        
        qimage = qimage2ndarray.array2qimage(self.displayPixmap,
                                             normalize = True)
        pixmap = QtGui.QPixmap(qimage)
        
        self._pixmapItem.setPixmap(pixmap)
#        self._pixmapItem.setOffset(-pixmap.width()/2.0,
#                                   -pixmap.height()/2.0)
#        self._pixmapItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
#        self.fitToWindow()

    #Event Handlers
    # ------------------------------------------------------------------
    
    def mouseHover(self, x,y, pixelValue):
        """Handle mouse move event of the mouseMoveEvent from underlying |QGraphicsView|.

        :param int x: Mouse x position
        :param int y: Mouse y position
        :param float val: value of pixmap at x,y """
        
#        if (x >= 0 and x < self.pixmap.width() and 
#            y >= 0 and y < self.pixmap.height()):
#        
#            val = self.pixmap.toImage().pixelColor(x,y).getRgb()
#            val = np.mean(val[:3])
        pixelValue = round(pixelValue, 5)
        self.valueLabel.updateValues(x,y, pixelValue)

    def handleWheelNotches(self, notches):
        """Handle wheel notch event from underlying |QGraphicsView|.

        :param float notches: Mouse wheel notches"""
        
        self.scaleImage(self._zoomFactorDelta ** notches)

    def closeEvent(self, event):
        """Overriden in order to disconnect scrollbar signals before
        closing.

        :param QEvent event: instance of a |QEvent|
        
        If this isn't done Python crashes!"""
        self.disconnectSbarSignals()
        super(ImageViewer, self).closeEvent(event)

    # ------------------------------------------------------------------

    def scaleImage(self, factor, combine=True):
        """Scale image by factor.

        :param float factor: either new :attr:`zoomFactor` or amount to scale
                             current :attr:`zoomFactor`

        :param bool combine: if ``True`` scales the current
                             :attr:`zoomFactor` by factor.  Otherwise
                             just sets :attr:`zoomFactor` to factor"""
        if not self._pixmapItem.pixmap():
            return

        if combine:
            self.zoomFactor = self.zoomFactor * factor
        else:
            self.zoomFactor = factor
#        self._view.checkTransformChanged()
        

    def dumpTransform(self):
        """Dump view transform to stdout."""
        self._view.dumpTransform(self._view.transform(), " "*4)


# ====================================================================