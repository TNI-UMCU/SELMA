# -*- coding: utf-8 -*-
"""
This module contains the following classes:
+ :class:`ValueHoverLabel`
+ :class:`SynchableGraphicsView`

@author: Cyrano
"""

# ====================================================================

from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

class ValueHoverLabel(QtWidgets.QLabel):
    """|QLabel| used for displaying x- and y-coordinates. """
    def __init__(self):
        QtWidgets.QLabel.__init__(self)
        self.xPos = 0
        self.yPos = 0
        self.value = 0
        
    def updateValues(self,x,y,val):
        self.xPos = x
        self.yPos = y
        self.value = val
        self._updateText()
        
    def _updateText(self):
        textString = "x = {},\n  y = {}, \n   val = {}".format(
                                                        self.xPos, 
                                                        self.yPos, 
                                                        self.value)
        self.setText( textString)
        

class SynchableGraphicsView(QtWidgets.QGraphicsView):
    """|QGraphicsView| that can synchronize panning & zooming of multiple
    instances.

    Also adds support for various scrolling operations and mouse wheel
    zooming."""

    def __init__(self, scene=None, parent=None):
        """:param scene: initial |QGraphicsScene|
        :type scene: QGraphicsScene or None
        :param QWidget: parent widget
        :type QWidget: QWidget or None"""
        if scene:
            super(SynchableGraphicsView, self).__init__(scene, parent)
        else:
            super(SynchableGraphicsView, self).__init__(parent)

        self._handDrag = False #disable panning view by dragging
        self.clearTransformChanges()
#        self.connectSbarSignals(self.scrollChanged)
        self.setMouseTracking(True)
        
        self.setTransformationAnchor
        
    # ------------------------------------------------------------------


    #Public Signals
    
    wheelEventSignal = QtCore.pyqtSignal(int)
    """ WheelEvent **Signal**.
    Emitted when the user triggers wheelEvent without any modifiers.
    
    :param int: direction of wheel.
    """

    #Private Signals

#    transformChanged = QtCore.pyqtSignal()
#    """Transformed Changed **Signal**.
#
#    Emitted whenever the |QGraphicsView| Transform matrix has been
#    changed."""
#    
#    scrollChanged = QtCore.pyqtSignal()
#    """Scroll Changed **Signal**.
#
#    Emitted whenever the scrollbar position or range has changed."""
    
    wheelNotches = QtCore.pyqtSignal(float)
    """Wheel Notches **Signal**.

    Emitted whenever the mouse wheel has been rolled. A wheelnotch is
    equal to wheel delta / 240"""
    
    
    def connectSbarSignals(self, slot):
        """Connect to scrollbar changed signals to synchronize panning.

        :param slot: slot to connect scrollbar signals to."""
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.UniqueConnection)
        #sbar.sliderMoved.connect(slot, type=QtCore.Qt.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

        sbar = self.verticalScrollBar()
        sbar.valueChanged.connect(slot, type=QtCore.Qt.UniqueConnection)
        #sbar.sliderMoved.connect(slot, type=QtCore.Qt.UniqueConnection)
        sbar.rangeChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

        #self.scrollChanged.connect(slot, type=QtCore.Qt.UniqueConnection)

    def disconnectSbarSignals(self):
        """Disconnect from scrollbar changed signals."""
        sbar = self.horizontalScrollBar()
        sbar.valueChanged.disconnect()
        #sbar.sliderMoved.disconnect()
        sbar.rangeChanged.disconnect()

        sbar = self.verticalScrollBar()
        sbar.valueChanged.disconnect()
        #sbar.sliderMoved.disconnect()
        sbar.rangeChanged.disconnect()

    # ------------------------------------------------------------------

    @property
    def handDragging(self):
        """Hand dragging state (*bool*)"""
        return self._handDrag

    @property
    def scrollState(self):
        """Tuple of percentage of scene extents
        *(sceneWidthPercent, sceneHeightPercent)*"""
        centerPoint = self.mapToScene(self.viewport().width()/2,
                                      self.viewport().height()/2)
        sceneRect = self.sceneRect()
        centerWidth = centerPoint.x() - sceneRect.left()
        centerHeight = centerPoint.y() - sceneRect.top()
        sceneWidth =  sceneRect.width()
        sceneHeight = sceneRect.height()

        sceneWidthPercent = centerWidth / sceneWidth if sceneWidth != 0 else 0
        sceneHeightPercent = centerHeight / sceneHeight if sceneHeight != 0 else 0
        return (sceneWidthPercent, sceneHeightPercent)

    @scrollState.setter
    def scrollState(self, state):
        sceneWidthPercent, sceneHeightPercent = state
        x = (sceneWidthPercent * self.sceneRect().width() +
             self.sceneRect().left())
        y = (sceneHeightPercent * self.sceneRect().height() +
             self.sceneRect().top())
        self.centerOn(x, y)

    @property
    def zoomFactor(self):
        """Zoom scale factor (*float*)."""
        return self.transform().m11()

    @zoomFactor.setter
    def zoomFactor(self, newZoomFactor):
        newZoomFactor = newZoomFactor / self.zoomFactor
        self.scale(newZoomFactor, newZoomFactor)

    # ------------------------------------------------------------------

    def wheelEvent(self, wheelEvent):
        """Overrides the wheelEvent to handle zooming. 
        Ensures that the cursor (more or less) stays on the same pixel when
        zooming. Doesn't work perfectly since the scrollbars have integer
        positions.

        :param QWheelEvent wheelEvent: instance of |QWheelEvent|"""
        
        assert isinstance(wheelEvent, QtGui.QWheelEvent)
        if wheelEvent.modifiers() & QtCore.Qt.ControlModifier:
            
            #don't magnify more than 60x
            if self.zoomFactor > 60 and wheelEvent.angleDelta().y() > 0: 
                return
            #don't shrink more than 10x
            if self.zoomFactor < 0.1 and wheelEvent.angleDelta().y() < 0: 
                return
            
            #Mouse position prior to zooming
            oldPos = self.mapToScene(wheelEvent.pos())
            
            #Zoom
            self.wheelNotches.emit(wheelEvent.angleDelta().y() / 240.0)
            wheelEvent.accept()

            # Get the new position
            newPos = self.mapToScene(wheelEvent.pos())
            
            # Calculate new scroll percentage
            delta = oldPos - newPos
            deltaSceneWidthPercent = (delta.x()) / self.sceneRect().width()
            deltaSceneHeightPercent = (delta.y()) / self.sceneRect().height()
            sceneWidthPercent, sceneHeightPercent = self.scrollState
            
            # Move to new position
            self.scrollState = (sceneWidthPercent + deltaSceneWidthPercent,
                                sceneHeightPercent + deltaSceneHeightPercent)
            
        else:
        #No modifier --> cycle through frames
#            super(SynchableGraphicsView, self).wheelEvent(wheelEvent)
            
            delta       = wheelEvent.angleDelta().y()
            if delta == 0:
                #only accept vertical scrolling
                return
            
            direction   = delta / abs(delta) 
            
            self.wheelEventSignal.emit(direction)
            wheelEvent.accept()
            

    def keyReleaseEvent(self, keyEvent):
        """Overrides to make sure key release passed on to other classes.

        :param QKeyEvent keyEvent: instance of |QKeyEvent|"""
        assert isinstance(keyEvent, QtGui.QKeyEvent)
        keyEvent.ignore()
        #super(SynchableGraphicsView, self).keyReleaseEvent(keyEvent)

    # ------------------------------------------------------------------

    def clearTransformChanges(self):
        """Reset view transform changed info."""
        self._transform = self.transform()

    def scrollToTop(self):
        """Scroll view to top."""
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToBottom(self):
        """Scroll view to bottom."""
        sbar = self.verticalScrollBar()
        sbar.setValue(sbar.maximum())

    def scrollToBegin(self):
        """Scroll view to left edge."""
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.minimum())

    def scrollToEnd(self):
        """Scroll view to right edge."""
        sbar = self.horizontalScrollBar()
        sbar.setValue(sbar.maximum())

    def centerView(self):
        """Center view."""
        sbar = self.verticalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())/2)
        sbar = self.horizontalScrollBar()
        sbar.setValue((sbar.maximum() + sbar.minimum())/2)

    def enableScrollBars(self, enable):
        """Set visiblility of the view's scrollbars.

        :param bool enable: True to enable the scrollbars """
        if enable:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def enableHandDrag(self, enable):
        """Set whether dragging the view with the hand cursor is allowed.

        :param bool enable: True to enable hand dragging """
        if enable:
            if not self._handDrag:
                self._handDrag = True
                self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            if self._handDrag:
                self._handDrag = False
                self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    # ------------------------------------------------------------------

