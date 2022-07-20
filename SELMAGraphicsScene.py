#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`ROIPolygonItem`
+ :class:`GraphicsScene`
+ :class:`SynchableGraphicsView`
+ :class:`ImageViewer`
+ :class:`SELMAMainWindow`

"""

# ====================================================================


import numpy as np
import qimage2ndarray

from PyQt5 import (QtCore, QtGui, QtWidgets)

# ====================================================================

class ROIPolygonItem(QtWidgets.QGraphicsPolygonItem):
    """|QGraphicsPolygonItem| that has information on whether it's used to add
    or subtract from the ROI.
    """
    def __init__(self, parent=None):
        super(ROIPolygonItem, self).__init__(parent)
        self._isAdd = True
        self.setZValue(1)
        
    def setIsAdd(self, isAdd):
        self._isAdd = isAdd
    
    def getIsAdd(self):
        return self._isAdd    



class GraphicsScene(QtWidgets.QGraphicsScene):
    """|QGraphicsScene| that can handle multiple mouse events to enable
    showing the value under the cursor as well as drawing ROIs.
    
    
    The graphics items are stored with the following zValues:
        -Pixmap       - 0
        -ROI          - 1
        -Vesselmask   - 2
    
    """
    
    def __init__(self, pixmapItem, parent=None):
        super(GraphicsScene, self).__init__(parent)
        
        self._contrastX     = 0
        self._contrastY     = 0
        self._contrast      = 0
        self._brightness    = 0
        
        #Keeps track if the scene is active
        self._active        = False
        
        self._initUI(pixmapItem)
    
    def _initUI(self, pixmapItem):
        """Set up UI elements that deal with drawing the ROIs."""
        
        self._pixmapItem            = pixmapItem
        self._maskPixmapItem        = QtWidgets.QGraphicsPixmapItem()
        self._vesselPixmapItem      = QtWidgets.QGraphicsPixmapItem()
        self.addItem(self._pixmapItem)
        self.addItem(self._maskPixmapItem)
        self.addItem(self._vesselPixmapItem)
        
        self._polygon               = QtGui.QPolygonF()
        self._currentPolygonItem    = None
        self._button                = None  
        self._mask                  = None
        
        self._maskBrush     = QtGui.QBrush(QtGui.QColor("#AA0000FF"))
        self._addBrush      = QtGui.QBrush(QtGui.QColor("#6000FF00"))
        self._subtractBrush = QtGui.QBrush(QtGui.QColor("#80FF0000"))
                                                        
        self._maskBrush.setStyle(QtCore.Qt.SolidPattern)
        self._addBrush.setStyle(QtCore.Qt.SolidPattern)
        self._subtractBrush.setStyle(QtCore.Qt.SolidPattern)
        
        self._pen = QtGui.QPen(QtGui.QColor("transparent"))  
        
    
    #Public:
    # =================================================================
    
    #Signals:
    mouseMove           = QtCore.pyqtSignal(int, int)
    updateProgressBar   = QtCore.pyqtSignal(int)
    adjustContrastSignal= QtCore.pyqtSignal(int, int)
    
    
    #Getters:
    def getMask(self):
        return self._mask
    
    
    #Setters:
    
    def setVesselMask(self, mask):
        """Adds a mask with the semgented vessels on top of the pixmap 
        and the ROIS.
        
        Args:
            mask (numpy.ndarray): binary mask.
        """
        
        #Turn the mask into a transparent pixmap with the color of _maskBrush
        maskr       = np.reshape(mask * self._maskBrush.color().redF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskg       = np.reshape(mask * self._maskBrush.color().greenF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskb       = np.reshape(mask * self._maskBrush.color().blueF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskalpha   = np.reshape(mask * self._maskBrush.color().alphaF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        
        mask = np.vstack((maskr, maskg, maskb, maskalpha))
        mask = np.swapaxes(mask, 0,2)
        mask = np.swapaxes(mask, 0,1)
        
        qimage = qimage2ndarray.array2qimage(mask, normalize = True)
        vesselMaskPixmap = QtGui.QPixmap(qimage)
        
        #Add the vesselMask to the scene
        self._vesselPixmapItem.setPixmap(vesselMaskPixmap)
        self._vesselPixmapItem.setOffset(-vesselMaskPixmap.width()  / 2.0,
                                         -vesselMaskPixmap.height() / 2.0)
        self._vesselPixmapItem.setZValue(2)
        self._vesselPixmapItem.show()
        
    
    def setMask(self, mask):
        """Sets a mask generated outside the program as the ROIs on top
        of the pixmap."""

        if mask is not None:
            self._mask = mask

        self.updateMaskPixmap()
        
    def resetMask(self):
        """Clears the mask of any ROIs."""
        
        if self._mask is None:
            return
        
        self._mask = np.zeros(self._mask.shape) != 0
        self.updateMaskPixmap()
        
    def resetContrast(self):
        """Resets the contrast and brightness to default values."""
        self._contrast      = 0
        self._brightness    = 0
        
    def setActive(self, active):
        """Sets the flag for the graphicsscene activity.  Drawing the ROIs
        only works if _active is True.
        
        Args: 
            active(bool)
        """
        self._active        = active
        
    
    #Events
    # =================================================================
        
    def mousePressEvent(self, event):
        """
        Overrides the mousePressEvent. Calls functions to create an ROIpolygon
        or change the contrast depending on the button that was pressed.
        
        LMB:        Start drawing ROI onto mask
        RMB:        Start removing ROI from mask
        MMB:        Start changing contrast
        
        """
        super(GraphicsScene, self).mousePressEvent(event)
        
        #find mouse button with which the event was called.
        if self._button is not None:
            return
        
        #Don't do anything if the scene is inactive.
        if not self._active:
            return

        #Call other functions based on the button that was pressed
        self._button = event.button()
        if self._button == QtCore.Qt.LeftButton or \
           self._button == QtCore.Qt.RightButton:
               
               self.startDrawing(event)
       
        elif self._button == QtCore.Qt.MiddleButton:
            self.startContrast(event)
        
        
    def mouseMoveEvent(self, event):
        """
        Overrides the mouseMoveEvent. Calls functions to draw an ROI
        or change the contrast depending on the button that was held down
        during mousemove.
        
        LMB:        add ROI to mask
        RMB:        remove ROI from mask
        MMB:        Change contrast
        
        Any / None: Update HoverLabel.
        
        """
        
        #Don't do anything if the scene is inactive.
        if not self._active:
            return
        
        #Call other functions based on the button that was pressed
        if self._button == QtCore.Qt.LeftButton or \
           self._button == QtCore.Qt.RightButton:
        
               self.continueDrawing(event)
       
        elif self._button == QtCore.Qt.MiddleButton:
            self.changeContrast(event)
       
        #update valueHoverLabel
        x,y = self.limitToSceneRect(event.scenePos())
        l = self.sceneRect().left()
        t = self.sceneRect().top()
        self.mouseMove.emit(x-l,y-t)
        
        super(GraphicsScene, self).mouseMoveEvent(event)
        
    
    def mouseReleaseEvent(self, event):
        """
        Overrides the mouseReleaseEvent. 
        Finishes drawing the ROI that needs to be added to / removed from
        the mask.         
        """
        
        #Don't do anything if the mousePressEvent wasn't valid.
        if self._button is None:
            return
        
        #Call other functions based on the button that was pressed
        if self._button == QtCore.Qt.LeftButton or \
           self._button == QtCore.Qt.RightButton:
               self.finishDrawing()
        
        super(GraphicsScene, self).mouseReleaseEvent(event)
        
        #Reset the button state.
        self._button    = None
        
    #Deal with mouse events
    #=================================================================
    
    def startDrawing(self, event):
        """
        Starts drawing an ROI. Keeps track of which button is being used as
        well as the start position.
        
        Args:
            event(QEvent): event object that was created on mousePressEvent.
        """
        
        #Make a new polygonItem to store the polygon
        x,y = self.limitToSceneRect(event.scenePos())
        self._currentPolygonItem = ROIPolygonItem()
        self._currentPolygonItem.setPen(self._pen)
        
        #Left mouse button - add a polygon to the ROI           
        if self._button == QtCore.Qt.LeftButton:
            self._currentPolygonItem.setIsAdd(True)    
            self._currentPolygonItem.setBrush(self._addBrush)
            
        #Right mouse button - subtract a polygon from the ROI          
        elif self._button == QtCore.Qt.RightButton:
            self._currentPolygonItem.setIsAdd(False) 
            self._currentPolygonItem.setBrush(self._subtractBrush)
            
        #Add the polygon to the scene
        self._polygon.append(QtCore.QPointF(x, y))
        self._currentPolygonItem.setPolygon(self._polygon)
        self.addItem(self._currentPolygonItem)
        
        
    def continueDrawing(self, event):
        """Adds the cursor position to the current polygon.
        
        Args:
            event(Qevent): event object that was created on mouseMoveEvent.
        """
        
        x,y = self.limitToSceneRect(event.scenePos())
        self.add4ConnectedXY(x,y)            
        
    def finishDrawing(self):
        """
        Finishes drawing the ROI and handles polygon addition / subtraction
        so that the ROI can be added to / subtracted from the mask.
        """
        
        #Only continue if the mousebutton was LMB or RMB.
        if self._button != QtCore.Qt.LeftButton and  \
           self._button != QtCore.Qt.RightButton:
            return
        
        #First, draw the polygon as 4-connected from the last point to the
        #start
        x = self._polygon[0].x()
        y = self._polygon[0].y()
        self.add4ConnectedXY(x,y)            
        self._currentPolygonItem.setPolygon(self._polygon)
        
        #Then, find the area underneath the current polygon.
        polygonMask = self.findROI()
        
        #Update the mask with the new ROI
        self.updateMask(polygonMask)
                
        #Resets the items until mouse is pressed again.
        self.removeItem(self._currentPolygonItem)
        self._currentPolygonItem    = None
        self._polygon               = QtGui.QPolygonF()

    def startContrast(self, event):
        """
        Finds the starting position of the cursor for changing the contrast.
        """
        
        x,y             = self.limitToSceneRect(event.scenePos())
        self._contrastX = x
        self._contrastY = y   
        
        #Save previous values        
        self._prevContrast      = self._contrast
        self._prevBrightness    = self._brightness
        
    def changeContrast(self, event):
        """Finds the difference between the event cursor position and the start
        position. Calculates the contrast and brightness based on that.
        
        Both range from -255 to 255. The values are scaled such that half
        of the sceneRect needs to be traversed in order to go from zero to
        max."""
        
        x,y             = self.limitToSceneRect(event.scenePos())
        
        dx              = x - self._contrastX
        dy              = y - self._contrastY
        
        dContrast       = 2 * 255 * dx / self.sceneRect().width()
        dBrightness     = 2 * 255 * dy / self.sceneRect().height()
        
        #Adjust contrast & brightness
        self._contrast      = self._prevContrast    + int(dContrast)
        self._brightness    = self._prevBrightness  + int(dBrightness) 
        
        #Truncate the values
        self._contrast      = max(self._contrast, -254)
        self._contrast      = min(self._contrast, 254)
        self._brightness    = max(self._brightness, -254)
        self._brightness    = min(self._brightness, 100)
        
        #Send signal to imageViewer
        self.adjustContrastSignal.emit(self._contrast,
                                       self._brightness)
        
        
    #Auxillary
    #=================================================================
    
    def findROI(self):
        """Finds the ROI of the polygon that was last drawn.
        
        Reads the pixels that are rendered in the graphicsScene
        and masks those that match the addBrush/subtractBrush color
        (depending on the isAdd property of the polygon.)
        
        Note: this method is pretty hacky, but still the most elegant 
        way so far. It ensures that the mask will be exactly as the 
        user sees it on screen. 
        For a more 'precise' version (with its own problems), see
        the commented version at the bottom of the file.
        """
    
        #Get screen dimensions
        dimX = int(self.sceneRect().right() - self.sceneRect().left())
        dimY = int(self.sceneRect().bottom() - self.sceneRect().top())
        
        #Prepare to render the graphicsScene to a QImage
        image       = QtGui.QImage(dimX,
                                   dimY,
                                   QtGui.QImage.Format_ARGB32_Premultiplied)
        painter     = QtGui.QPainter(image)
        
        #hide pixmap
        self._pixmapItem.hide()
        
        #Render the image on the screen (without the pixmap) to the painter.
        self.render(painter, QtCore.QRectF(), QtCore.QRectF())
        painter.end()
        
        #show pixmap
        self._pixmapItem.show()
        
        #Get array from QImage
        bitBuffer   = image.bits()
        bitBuffer.setsize(dimX * dimY * 4)
        arr = np.frombuffer(bitBuffer, np.uint8)
        arr = np.reshape(arr, (dimX, dimY,4))
        
        #Mask out ROIs
        #Note: colors are [b,g,r,alpha] (apparently)
        if self._currentPolygonItem.getIsAdd():
            roiColor        = self._addBrush.color()
            maskValue       = roiColor.green() * roiColor.alpha() / 255
            polygonMask     = arr[:,:,1] == maskValue
        else:
            roiColor        = self._subtractBrush.color()
            maskValue       = roiColor.red() * roiColor.alpha() / 255
            polygonMask     = arr[:,:,2] == maskValue
        
        return polygonMask
        
    def updateMask(self, polygonMask):
        """Takes the drawn ROI and adds / subtracts it from the mask."""
        
        if self._mask is None:
            self._mask = np.zeros(
                                (int(self.sceneRect().width()), 
                                 int(self.sceneRect().height())
                                 ))
        
        self._mask  = self._mask.astype(np.uint8)
        polygonMask = polygonMask.astype(np.int8)
        
        if self._currentPolygonItem.getIsAdd():
            mask        = self._mask + polygonMask
        else:
            mask        = self._mask - polygonMask
            
        self._mask      = mask > 0
        #Updates the pixmapItem containing the mask
        self.updateMaskPixmap()
        
        
    
    def limitToSceneRect(self, point):
        """Limits a given point to the sceneRect."""
        x = point.x()
        y = point.y()
        
        x = max(self.sceneRect().left() + 1, x)
        x = min(self.sceneRect().right() - 1, x)
        
        y = max(self.sceneRect().top() + 1, y)
        y = min(self.sceneRect().bottom() - 1, y)     
        
        x = int(np.round(x))
        y = int(np.round(y))
                    
        return x,y
    
    def add4ConnectedXY(self, x, y):
        """Adds points to the polygon to ensure that the border is
        4-connected."""
                
        polygon = self._polygon
        
        #First point in polygon
        if len(polygon) == 0:
            polygon.append(QtCore.QPointF(x,y))
        
        #Find the current and last points        
        x2 = x
        y2 = y
        x1 = polygon[-1].x()
        y1 = polygon[-1].y()
        x0 = x1
        y0 = y1
        
        if polygon.size() > 1:
            x0 = polygon[-2].x()
            y0 = polygon[-2].y()
        
        #numSteps is the distance between the current and last points
        numSteps = abs(x2 - x1) + abs(y2 - y1)
        
        while numSteps > 1: 
            
            deltaX = x2 - x1
            deltaY = y2 - y1
            deltaXPrev = int(x0 - x1)
            deltaYPrev = int(y0 - y1)
            
            signX = np.sign(deltaX)
            signY = np.sign(deltaY)
            
            #What direction should the next step be in
            #TODO, rewrite
            if abs(deltaY) > abs(deltaX):
                polygon.append(QtCore.QPointF(x1, y1 + signY))     
                y1 = y1 + signY
            elif abs(deltaX) > abs(deltaY):
                polygon.append(QtCore.QPointF(x1 + signX, y1))  
                x1 = x1 + signX
            elif deltaYPrev == 0:
                polygon.append(QtCore.QPointF(x1, y1 + signY)) 
                y1 = y1 + signY
            elif deltaXPrev == 0:
                polygon.append(QtCore.QPointF(x1 + signX, y1))      
                x1 = x1 + signX
            else:
                polygon.append(QtCore.QPointF(x1 + signX, y1))
                x1 = x1 + signX
            
            numSteps -= 1
        
        #If numSteps == 1, then it's 4-connected.
        polygon.append(QtCore.QPointF(x, y))  
        self._currentPolygonItem.setPolygon(self._polygon)
    
    
    def updateMaskPixmap(self):
        """Updates the mask used in the maskPixmapItem. Doesn't make a new 
        pixmapitem."""
        
        
        mask = self._mask.astype(np.uint8)*255
        
        #Turn the mask into a transparent pixmap with the color of _addBrush
        maskr       = np.reshape(mask * self._addBrush.color().redF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskg       = np.reshape(mask * self._addBrush.color().greenF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskb       = np.reshape(mask * self._addBrush.color().blueF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        maskalpha   = np.reshape(mask * self._addBrush.color().alphaF(),
                                 (1,mask.shape[0], mask.shape[1])
                                 )
        
        mask = np.vstack((maskr, maskg, maskb, maskalpha))
        mask = np.swapaxes(mask, 0,2)
        mask = np.swapaxes(mask, 0,1)
        
        #Make it into a pixmap.
        qimage = qimage2ndarray.array2qimage(mask, normalize = True)
        self._maskPixmap = QtGui.QPixmap(qimage)
        
        #Update the pixmapItem.
        self._maskPixmapItem.setPixmap(self._maskPixmap)
        self._maskPixmapItem.setOffset(-self._maskPixmap.width()/2.0,
                             -self._maskPixmap.height()/2.0)
#        self._maskPixmapItem.setTransformationMode(
#            QtCore.Qt.SmoothTransformation)
        self._maskPixmapItem.setZValue(1)
        
        
"""     #====================================================
Multiprocessed method to find the area in a polygon using the 
polygon.contains() function. Takes long, gives strange results.
"""
        
#        #Make a canvas with coordinates
#        x, y = np.meshgrid(np.arange(dimX), np.arange(dimY)) 
#        x, y = x.flatten(), y.flatten()
#        points = np.vstack((x,y)).T     
#        
#        #find cpu cores
#        nCores          = cpu_count()
#        pointsPerCore   = int(len(points) / nCores)
#        
#        #Make path object from the polygon vertices.
#        newPolygon = QtGui.QPolygonF()
#        for item in self.items():
#                if isinstance(item, ROIPolygonItem):
#                    print(len(item.polygon()))
#                    newPolygon= newPolygon.united(item.polygon())
#        
#        vertices = []
#        for point in newPolygon:
#            x = point.x() - self.sceneRect().left()
#            y = point.y() - self.sceneRect().top()
#            
#            vertices.append( (x,y) )
#            
#        #Check if the mask is empty.
#        if len(vertices) == 0:
#            mask = np.ones((dimX, dimY))
#            return mask
#            
#        path = Path(vertices)
#        
#        #Split the coordinates one list per cpu core.
#        objList = []
#        for i in range(nCores):
#            obj = (path,
#                   points[i * pointsPerCore : (i+1) * pointsPerCore ])
#            objList.append(obj)
#        
#        freeze_support() #prevent multiprocessing from freezing
#        with Pool(nCores) as pool:
#            res = pool.map(containsPoints, objList)
#
#        #concatenate and reshape result.
#        grid = np.concatenate(res)            
#        mask = np.asarray(grid).reshape(dimX, dimY)
#        print(np.sum(mask))
#        
#        import matplotlib.pyplot as plt
#        
#        fig, ax = plt.subplots()
#        fig.set_size_inches(10,10)
#        ax.imshow(mask)
#        
#        return mask
    


#    def containsPoints(obj):
#            
#        path, points = obj
#        
#        #Find all pixels in polygon.
#        grid = path.contains_points(points)
#            
#        return grid