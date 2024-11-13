#!/usr/bin/env python

"""
This module contains the following classes:

+ :class:`SelmaSettings`

"""

# ====================================================================

from PyQt5 import (QtCore, QtGui, QtWidgets)
import os
import SELMAGUIBar

# ====================================================================
class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


def getInfo():
    """Reads the name, companyname and version number from info.txt and 
    returns them."""
    
    fn = "info.txt"
    fullpath = os.path.join(os.getcwd(), fn)
    
    with open (fullpath, "r") as info:
        data=info.readlines()
        company     = data[0]
        appname     = data[1]
        version     = data[2]
        
        return company, appname, version
    

class SelmaSettings(QtWidgets.QWidget):
    """
    This class contains the UI for interacting with the user settings. 
    Settings are viewed, edited and saved.
    
    The settings window displays the following tabs:
        General         - for the main functioning of the program
        Ghosting        - for the removeGhosting function
        Perpendicular   - for the removeNonPerpendicular function
        Reset           - for resetting the settings to their default
    """
    #Signals
    thresholdSignal     = QtCore.pyqtSignal() 
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        
        #Create window
        self.initGui()
        
        #Load settings from disk    - is done in self.show()
        # self.getSettings()
    
    def initGui(self):
        
        self.setGeometry(QtCore.QRect(100, 100, 450, 200))
        self.setWindowTitle("Settings")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        
        #Add tabs
        self.tabs           = QtWidgets.QTabWidget()
        self.mainTab        = QtWidgets.QWidget()
        #self.structureTab   = QtWidgets.QWidget()
        self.ghostingTab    = QtWidgets.QWidget()
        self.nonPerpTab     = QtWidgets.QWidget()
        self.deduplicateTab = QtWidgets.QWidget()
        self.segmentTab     = QtWidgets.QWidget()
        #self.clusteringTab  = QtWidgets.QWidget()
        self.resetTab       = QtWidgets.QWidget()
        
        self.tabs.addTab(self.mainTab,          "General")
        #self.tabs.addTab(self.structureTab,     "Structure")
        self.tabs.addTab(self.ghostingTab,      "Ghosting")
        self.tabs.addTab(self.nonPerpTab,       "Non-Perp")
        self.tabs.addTab(self.deduplicateTab,   "Deduplicate")
        self.tabs.addTab(self.segmentTab,       "Segment")
        #self.tabs.addTab(self.clusteringTab,    "Advanced Clustering")
        self.tabs.addTab(self.resetTab,         "Reset")
        
        #Design Tabs
        self.initMainTab()
        # self.initStructureTab()
        self.initGhostingTab()
        self.initNonPerpTab()
        self.initDeduplicateTab()
        self.initSegmentTab()
        # self.initClusteringTab()
        self.initResetTab()
        
        #Add to layout
        self.layout         = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        
        #Buttons
        self.okButton       = QtWidgets.QPushButton("OK")
        self.cancelButton   = QtWidgets.QPushButton("Cancel")
        self.applyButton    = QtWidgets.QPushButton("Apply")
        self.okButton.pressed.connect(self.okButtonPushed)
        self.cancelButton.pressed.connect(self.close)
        self.applyButton.pressed.connect(self.applySettings)
        
        self.buttonLayout   = QtWidgets.QHBoxLayout(self)
        self.buttonLayout.addWidget(self.applyButton)
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.layout.addLayout(self.buttonLayout)
        
        #Error Label
        self.errorLabel     = QtWidgets.QLabel("")
        self.errorLabel.setStyleSheet("QLabel {color: red }")
        self.layout.addWidget(self.errorLabel)
        
        #Finish
        self.setLayout(self.layout)
        
        
    def show(self):         #override super function to always fetch settings
        self.getSettings()
        QtWidgets.QWidget.show(self)
        
        
    def initMainTab(self):
        """The tab containing the general settings.        """
        
        self.mainTab.medDiamEdit                = QtWidgets.QLineEdit()
        self.mainTab.confidenceInterEdit        = QtWidgets.QLineEdit()
#        self.mainTab.whiteMatterProbEdit       = QtWidgets.QLineEdit()
        self.mainTab.mmVencBox                  = QtWidgets.QCheckBox()
        self.mainTab.gaussianSmoothingBox       = QtWidgets.QCheckBox()
        self.mainTab.ignoreOuterBandBox         = QtWidgets.QCheckBox()
        self.mainTab.decimalCommaBox            = QtWidgets.QCheckBox()
        self.mainTab.mmPixelBox                 = QtWidgets.QCheckBox()
        self.mainTab.manualSelectionBox         = QtWidgets.QCheckBox()
        
        self.mainTab.label1     = QtWidgets.QLabel("Median filter diameter")
        self.mainTab.label2     = QtWidgets.QLabel("Confindence interval")
        self.mainTab.label3     = QtWidgets.QLabel("mm")
        self.mainTab.label4     = QtWidgets.QLabel("vEnc in mm")
        self.mainTab.label5     = QtWidgets.QLabel(
            "Use Gaussian smoothing\ninstead of median filter")
        self.mainTab.label6     = QtWidgets.QLabel(
            "Ignore the outer 80 pixels\nof the image.")
        self.mainTab.label7     = QtWidgets.QLabel(
            "Use a decimal comma in the\noutput instead of a dot.")
        self.mainTab.label8     = QtWidgets.QLabel(
            "Use manual vessel selection (overrides Non-Perp and Deduplicate).")
        
        self.mainTab.label1.setToolTip(
            "Diameter of the kernel used in the median filtering operations.")
        self.mainTab.label2.setToolTip(
            "Confidence interval used to determine whether a vessel is" + 
            " significant. \nDefault is 0.05.")
        self.mainTab.label3.setToolTip(
            "Select whether the diameter is in mm. If off, diameter is in" +
            " pixels. \n If in mm, diameter gets rounded up to the nearest" +
            "odd pixel value.")
        self.mainTab.label4.setToolTip(
            "Select whether the velocity encoding is in mm/s, default is " +
            "cm/s. If turned on, the velocity encoding will be converted to" +
            "cm/s while loading the images.")
        self.mainTab.label5.setToolTip(
            "Speeds up analysis drastically, might yield inaccurate results."+
            "\nUse only for testing.")
        self.mainTab.label6.setToolTip(
            "Removes the outer 80 pixels at each edge from the mask. ")
        self.mainTab.label8.setToolTip(
            "Override standard remove non-perpendicular and deduplication\n" +
            " algorithms with manual selection of vessels. This function\n" +
            " is currently not applicable with batch analysis.")

        #Add items to layout
        self.mainTab.layout     = QtWidgets.QGridLayout()
        self.mainTab.layout.addWidget(self.mainTab.medDiamEdit, 0,0)
        self.mainTab.layout.addWidget(self.mainTab.mmPixelBox, 0,2)
        self.mainTab.layout.addWidget(self.mainTab.confidenceInterEdit, 1,0)
        
        self.mainTab.layout.addWidget(QHLine(),               3,0,1,2)
        
        self.mainTab.layout.addWidget(self.mainTab.mmVencBox,
                                      4,0)
        self.mainTab.layout.addWidget(self.mainTab.gaussianSmoothingBox,
                                      5,0)
        self.mainTab.layout.addWidget(self.mainTab.ignoreOuterBandBox,
                                      6,0)
        self.mainTab.layout.addWidget(self.mainTab.decimalCommaBox,
                                      7,0)
        self.mainTab.layout.addWidget(self.mainTab.manualSelectionBox,
                                      8,0)
        
        #Add labels to layout
        self.mainTab.layout.addWidget(self.mainTab.label1,      0,1)
        self.mainTab.layout.addWidget(self.mainTab.label2,      1,3)
        self.mainTab.layout.addWidget(self.mainTab.label3,      0,3)
        self.mainTab.layout.addWidget(self.mainTab.label4,      4,3)
        self.mainTab.layout.addWidget(self.mainTab.label5,      5,3)
        self.mainTab.layout.addWidget(self.mainTab.label6,      6,3)
        self.mainTab.layout.addWidget(self.mainTab.label7,      7,3)
        self.mainTab.layout.addWidget(self.mainTab.label8,      8,3)
        
        self.mainTab.setLayout(self.mainTab.layout)
        
    # def initStructureTab(self):
    #     """The tab containing the structure settings.        """
        
    #     self.structureTab.BasalGangliaButton         = QtWidgets.QRadioButton()
    #     self.structureTab.SemiovalCentreButton       = QtWidgets.QRadioButton()
    #     self.structureTab.AdvancedClusteringButton   = QtWidgets.QRadioButton()
        
    #     self.structureTab.label1     = QtWidgets.QLabel(
    #         "Perform analysis on basal ganglia")
    #     self.structureTab.label2     = QtWidgets.QLabel(
    #         "Perform analysis on semioval centre")
    #     self.structureTab.label3     = QtWidgets.QLabel(
    #         "Use custom clustering settings from advanced clustering menu. "
    #         + "\nThis action overrides standard structure settings")
        
    #     self.structureTab.label1.setToolTip(
    #         "Select this box for analysis on basal ganglia data")
    #     self.structureTab.label2.setToolTip(
    #         "Select this box for analysis on white matter data")
    #     self.structureTab.label3.setToolTip(
    #         "Select this box if you want to override standard structures with"
    #         + " custom clustering settings")
        
    #     #Add items to layout
    #     self.structureTab.layout     = QtWidgets.QGridLayout()
    #     self.structureTab.layout.addWidget(
    #         self.structureTab.BasalGangliaButton ,
    #                                   0,0)
    #     self.structureTab.layout.addWidget(
    #         self.structureTab.SemiovalCentreButton ,
    #                                   1,0)
    #     self.structureTab.layout.addWidget(
    #         self.structureTab.AdvancedClusteringButton,
    #                                   3,0)
        
    #     #Add labels to layout
    #     self.structureTab.layout.addWidget(self.structureTab.label1,      0,3)
    #     self.structureTab.layout.addWidget(self.structureTab.label2,      1,3)
    #     self.structureTab.layout.addWidget(self.structureTab.label3,      3,3)
        
    #     self.structureTab.setLayout(self.structureTab.layout)
        
    def initGhostingTab(self): 
        """The tab containing the removeGhosting settings."""

        #Toggle Ghosting
        self.ghostingTab.doGhostingBox      = QtWidgets.QCheckBox()
        
        #Inputs
        self.ghostingTab.noVesselThreshEdit     = QtWidgets.QLineEdit()
        self.ghostingTab.smallVesselThreshEdit  = QtWidgets.QLineEdit()
        self.ghostingTab.smallVesselExclXEdit   = QtWidgets.QLineEdit()
        self.ghostingTab.smallVesselExclYEdit   = QtWidgets.QLineEdit()
        self.ghostingTab.largeVesselExclXEdit   = QtWidgets.QLineEdit()
        self.ghostingTab.largeVesselExclYEdit   = QtWidgets.QLineEdit()
        self.ghostingTab.brightVesselPercEdit   = QtWidgets.QLineEdit()
        
        #Labels
        self.ghostingTab.label0 = QtWidgets.QLabel(
            "Exclude ghosting zones")
        self.ghostingTab.label1 = QtWidgets.QLabel(
            "Vessel thresholds small vessel & large vessel")
        self.ghostingTab.label2 = QtWidgets.QLabel(
            "Small vessel exclusion zone X, Y")
        self.ghostingTab.label3 = QtWidgets.QLabel(
            "Large vessel exclusion zone X, Y")
        self.ghostingTab.label4 = QtWidgets.QLabel(
            "Bright pixel percentile")
        
        #Tooltips
        self.ghostingTab.label0.setToolTip(
            "When toggled on, the areas near particulary"   +
            " bright vessels are excluded from analysis.")
        self.ghostingTab.label1.setToolTip(
            "Thresholds for qualifying as a small or large vessel. "    +
            "\nAnything smaller than a small vessel is considered not "+
            "to be a vessel.")
        self.ghostingTab.label2.setToolTip(
            "The ghosting zone around a small vessel is increased in the"+
            " X- and Y-directions by this much.")
        self.ghostingTab.label3.setToolTip(
            "The ghosting zone around a large vessel is increased in the"+
            " X- and Y-directions by this much.")
        self.ghostingTab.label4.setToolTip(
            "What percentage intensity a voxel needs to have in order to"+
            " be classified as a bright vessel.")
        
        
        #Add to layout
        self.ghostingTab.layout     = QtWidgets.QGridLayout()
        self.ghostingTab.layout.addWidget(self.ghostingTab.doGhostingBox,
                                          0,0)
        
        self.ghostingTab.layout.addWidget(QHLine(),                   
                                          1,0,1,4)
        
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.noVesselThreshEdit, 2,0)
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.smallVesselThreshEdit, 2,1)
        
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.smallVesselExclXEdit, 3,0)
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.smallVesselExclYEdit, 3,1)
        
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.largeVesselExclXEdit, 4,0)
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.largeVesselExclYEdit, 4,1)
        
        self.ghostingTab.layout.addWidget(
            self.ghostingTab.brightVesselPercEdit, 5,0)

        self.ghostingTab.layout.addWidget(self.ghostingTab.label0,    0,3)
        self.ghostingTab.layout.addWidget(self.ghostingTab.label1,    2,3)
        self.ghostingTab.layout.addWidget(self.ghostingTab.label2,    3,3)
        self.ghostingTab.layout.addWidget(self.ghostingTab.label3,    4,3)
        self.ghostingTab.layout.addWidget(self.ghostingTab.label4,    5,3)
        
        self.ghostingTab.setLayout(self.ghostingTab.layout)
        
    def initNonPerpTab(self):
        """The tab containing the removeGhosting settings."""

        #Toggle nonPerp
        self.nonPerpTab.removeNonPerpBox            = QtWidgets.QCheckBox()
        self.nonPerpTab.onlyMPosBox                 = QtWidgets.QCheckBox()
        #Inputs
        self.nonPerpTab.minScalingEdit              = QtWidgets.QLineEdit()
        self.nonPerpTab.maxScalingEdit              = QtWidgets.QLineEdit()
        self.nonPerpTab.windowSizeEdit              = QtWidgets.QLineEdit()
        self.nonPerpTab.magnitudeThreshEdit         = QtWidgets.QLineEdit()
        self.nonPerpTab.ratioThreshEdit             = QtWidgets.QLineEdit()
        
        #Labels
        self.nonPerpTab.label0 = QtWidgets.QLabel(
            "Exclude non-perpendicular zones.")
        self.nonPerpTab.label1 = QtWidgets.QLabel(
            "Only look at positive magnitude.")
        self.nonPerpTab.label2 = QtWidgets.QLabel(
            "Min and Max scaling")
        self.nonPerpTab.label3 = QtWidgets.QLabel(
            "Window size for measuring vessel shape.")
        self.nonPerpTab.label4 = QtWidgets.QLabel(
            "Magnitude threshold for measuring vessel shape.")
        self.nonPerpTab.label5 = QtWidgets.QLabel(
            "Major / minor axis threshold ratio.")
        
        #Tooltips        
        self.nonPerpTab.label0.setToolTip(
            "When toggled on, the significant vessels"   +
            " are filtered for any vessels that lie \n"  +
            "non-perpendicular to the imaging plane.")
        self.nonPerpTab.label1.setToolTip(
            "When toggled on, only vessels with positive magnitude will" +
            "be filtered.")
        self.nonPerpTab.label2.setToolTip(
            "Min and max scaling adjustments. See readme.")
        self.nonPerpTab.label3.setToolTip(
            "The vessel shape is measured in a window around each cluster."+
            "This is the window radius.")
        self.nonPerpTab.label4.setToolTip(
            "The vessel shape is measured on the\nmagnitude data." +
            " This is the magnitude\nthreshold for vessels.")
        self.nonPerpTab.label5.setToolTip(
            "The criterion for exlusion is: major radius / minor radius "+
            " > X.\n This is X")
        
        #Add to layout
        self.nonPerpTab.layout              = QtWidgets.QGridLayout()
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.removeNonPerpBox,
            0,0)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.onlyMPosBox,
            1,0)
        self.nonPerpTab.layout.addWidget(
            QHLine(),
            2,0,1,4)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.minScalingEdit,
            3,0)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.maxScalingEdit,
            3,1)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.windowSizeEdit,
            4,0)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.magnitudeThreshEdit,
            5,0)
        self.nonPerpTab.layout.addWidget(
            self.nonPerpTab.ratioThreshEdit,
            6,0)  
        
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label0,    0,3)
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label1,    1,3)
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label2,    3,3)
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label3,    4,3)
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label4,    5,3)
        self.nonPerpTab.layout.addWidget(self.nonPerpTab.label5,    6,3)
        
        self.nonPerpTab.setLayout(self.nonPerpTab.layout)
        
        
    def initDeduplicateTab(self):
        
        self.deduplicateTab.deduplicateBox          = QtWidgets.QCheckBox()
        self.deduplicateTab.deduplicateRangeEdit    = QtWidgets.QLineEdit()
        
        self.deduplicateTab.label0                  = QtWidgets.QLabel(
            "Deduplicate vessels")
        self.deduplicateTab.label1                  =QtWidgets.QLabel(
            "Deduplication range")
        
        self.deduplicateTab.label0.setToolTip(
            "When toggled on, vessels that are very close to eachother"+ 
            "will be excluded.")
        

        #Add items to layout
        self.deduplicateTab.layout                  = QtWidgets.QGridLayout()
        self.deduplicateTab.layout.addWidget(
            self.deduplicateTab.deduplicateBox, 0,0)
        self.deduplicateTab.layout.addWidget(
            QHLine(),            1,0,1,2)
        self.deduplicateTab.layout.addWidget(
            self.deduplicateTab.deduplicateRangeEdit, 2,0)
        
        #Add labels to layout
        self.deduplicateTab.layout.addWidget(self.deduplicateTab.label0,      
                                             0,1)
        self.deduplicateTab.layout.addWidget(self.deduplicateTab.label1,      
                                             2,1)
        
        self.deduplicateTab.setLayout(self.deduplicateTab.layout)
        
        
    def initSegmentTab(self):
        
        self.segmentTab.whiteMatterProb            = QtWidgets.QLineEdit()
        
        self.segmentTab.label1     = QtWidgets.QLabel(
            "White matter probability")

        #Add items to layout
        self.segmentTab.layout     = QtWidgets.QGridLayout()
        self.segmentTab.layout.addWidget(
            self.segmentTab.whiteMatterProb, 0,0)
        
        #Add labels to layout
        self.segmentTab.layout.addWidget(self.segmentTab.label1,      0,1)
        
        self.segmentTab.setLayout(self.segmentTab.layout)
        
    # def initClusteringTab(self):
    #     """The tab containing the cluster settings.        """
        
    #     self.clusteringTab.PositiveMagnitudeBox         = QtWidgets.QCheckBox()
    #     self.clusteringTab.NegativeMagnitudeBox         = QtWidgets.QCheckBox()
    #     self.clusteringTab.IsointenseMagnitudeBox       = QtWidgets.QCheckBox()
    #     self.clusteringTab.PositiveFlowBox              = QtWidgets.QCheckBox()
    #     self.clusteringTab.NegativeFlowBox              = QtWidgets.QCheckBox()
        
    #     self.clusteringTab.label1     = QtWidgets.QLabel(
    #         "Include clusters with significant positive magnitude")
    #     self.clusteringTab.label2     = QtWidgets.QLabel(
    #         "Include clusters with significant negative magnitude")
    #     self.clusteringTab.label3     = QtWidgets.QLabel(
    #         "Include clusters with significant isointense magnitude")
    #     self.clusteringTab.label4     = QtWidgets.QLabel(
    #         "Include clusters with significant positive velocity")
    #     self.clusteringTab.label5     = QtWidgets.QLabel(
    #         "Include clusters with significant negative velocity")
        
    #     self.clusteringTab.label1.setToolTip(
    #         "Include clusters of significant flow voxels with positive" + 
    #         " magnitude in analysis")
    #     self.clusteringTab.label2.setToolTip(
    #         "Include clusters of significant flow voxels with negative" + 
    #         " magnitude in analysis")
    #     self.clusteringTab.label3.setToolTip(
    #         "Include clusters of significant flow voxels with isointense" + 
    #         " magnitude in analysis")
    #     self.clusteringTab.label4.setToolTip(
    #         "Include clusters with significant flow and positive" + 
    #         " direction in analysis")
    #     self.clusteringTab.label5.setToolTip(
    #         "Include clusters with significant flow and negative" + 
    #         " direction in analysis")

    #     #Add items to layout
    #     self.clusteringTab.layout     = QtWidgets.QGridLayout()
    #     self.clusteringTab.layout.addWidget(
    #         self.clusteringTab.PositiveMagnitudeBox ,
    #                                   0,0)
    #     self.clusteringTab.layout.addWidget(
    #         self.clusteringTab.NegativeMagnitudeBox,
    #                                   1,0)
    #     self.clusteringTab.layout.addWidget(
    #         self.clusteringTab.IsointenseMagnitudeBox,
    #                                   2,0)
        
    #     self.clusteringTab.layout.addWidget(QHLine(),                   
    #                                       3,0,1,4)
        
    #     self.clusteringTab.layout.addWidget(
    #         self.clusteringTab.PositiveFlowBox ,
    #                                   4,0)
    #     self.clusteringTab.layout.addWidget(
    #         self.clusteringTab.NegativeFlowBox,
    #                                   5,0)
        
    #     #Add labels to layout
    #     self.clusteringTab.layout.addWidget(self.clusteringTab.label1,  0,3)
    #     self.clusteringTab.layout.addWidget(self.clusteringTab.label2,  1,3)
    #     self.clusteringTab.layout.addWidget(self.clusteringTab.label3,  2,3)
    #     self.clusteringTab.layout.addWidget(self.clusteringTab.label4,  4,3)
    #     self.clusteringTab.layout.addWidget(self.clusteringTab.label5,  5,3)
        
    #     self.clusteringTab.setLayout(self.clusteringTab.layout)
        
    def initResetTab(self):
        self.resetTab.resetButton   = QtWidgets.QPushButton("Reset settings")
        self.resetTab.resetButton.setToolTip(
                "Resets all settings to their default value.")
        self.resetTab.resetButton.pressed.connect(self.reset)
        
        self.resetTab.layout        = QtWidgets.QHBoxLayout()
        self.resetTab.layout.addWidget(self.resetTab.resetButton)
        self.resetTab.setLayout(self.resetTab.layout)
        
        
    def getSettings(self):
        """
        Loads the settings from the QSettings object that is saved with the 
        application and stores them in the UI.
        """
        
        COMPANY, APPNAME, version = getInfo()
        COMPANY             = COMPANY.split()[0]
        APPNAME             = APPNAME.split()[0]
        settings = QtCore.QSettings(COMPANY, APPNAME)
        
        #General settings
        #==========================================
        
        #medDiam
        medDiam                 = settings.value("medDiam")
        if medDiam is None:
            medDiam             = 10
        self.mainTab.medDiamEdit.setText(str(medDiam))
        
        mmPixel                 = settings.value("mmPixel")
        if mmPixel is None:
            mmPixel     = True
        else:
            mmPixel = mmPixel == 'true'
        self.mainTab.mmPixelBox.setChecked(mmPixel)
        
        #confidence interval
        confidenceInter         = settings.value("confidenceInter")
        if confidenceInter is None:
            confidenceInter     = 0.05
        self.mainTab.confidenceInterEdit.setText(str(confidenceInter))
        
        #white matter probability
#        whiteMatterProb         = settings.value("whiteMatterProb")
#        if whiteMatterProb is None:
#            whiteMatterProb     = 0.5
#        self.mainTab.whiteMatterProbEdit.setText(str(whiteMatterProb))
        
        #average over cardiac cycle
        mmVenc     = settings.value("mmVenc")
        if mmVenc is None:
            mmVenc = False
        else:
            mmVenc = mmVenc == 'true'
        self.mainTab.mmVencBox.setChecked(mmVenc)
        
        #Do Gaussian smoothing - default is False
        gaussianSmoothing       = settings.value("gaussianSmoothing")
        if gaussianSmoothing is None:
            gaussianSmoothing   = False
        else:
            gaussianSmoothing   = gaussianSmoothing == 'true'
        self.mainTab.gaussianSmoothingBox.setChecked(gaussianSmoothing)
        
        #Ignore outer band
        ignoreOuterBand         = settings.value("ignoreOuterBand")
        if ignoreOuterBand is None:
            ignoreOuterBand = False
        else:
            ignoreOuterBand     = ignoreOuterBand == 'true'
        self.mainTab.ignoreOuterBandBox.setChecked(ignoreOuterBand)
        
        #Use decimal comma
        decimalComma         = settings.value("decimalComma")
        if decimalComma is None:
            decimalComma = False
        else:
            decimalComma     = decimalComma == 'true'
        self.mainTab.decimalCommaBox.setChecked(decimalComma)
        
        #Use manual selection
        manualSelection      = settings.value("manualSelection")
        if manualSelection is None:
            manualSelection = False
        else:
            manualSelection     = manualSelection == 'true'
        self.mainTab.manualSelectionBox.setChecked(manualSelection)
        
        
        #Structure settings
        #=============================================
        
        # #Select analysis for basal ganglia data
        # BasalGanglia       = settings.value("BasalGanglia")
        # if BasalGanglia is None:
        #     BasalGanglia   = False
        # else:
        #     BasalGanglia   = BasalGanglia == 'true'
        # self.structureTab.BasalGangliaButton.setChecked(BasalGanglia)
        
        # #Select analysis for white matter data
        # SemiovalCentre       = settings.value("SemiovalCentre")
        # if SemiovalCentre is None:
        #     SemiovalCentre   = False
        # else:
        #     SemiovalCentre   = SemiovalCentre == 'true'
        # self.structureTab.SemiovalCentreButton.setChecked(SemiovalCentre)
        
        # #Enable custom clustering for advanced users
        # AdvancedClustering    = settings.value("AdvancedClustering")
        # if AdvancedClustering is None:
        #     AdvancedClustering   = False
        # else:
        #     AdvancedClustering   = AdvancedClustering == 'true'
        # self.structureTab.AdvancedClusteringButton.setChecked(
        #     AdvancedClustering)
        
        
        #Ghosting settings
        #=============================================
        
        #perform the ghosting filter
        doGhosting = settings.value("doGhosting")
        if doGhosting is None:
            doGhosting = True
        else:
            doGhosting = doGhosting == 'true'
        self.ghostingTab.doGhostingBox.setChecked(doGhosting)
        
        
        #Vessel thresholds
        noVesselThresh = settings.value("noVesselThresh")
        if noVesselThresh is None:
            noVesselThresh = 5
        self.ghostingTab.noVesselThreshEdit.setText(str(noVesselThresh))
        
        smallVesselThresh = settings.value("smallVesselThresh")
        if smallVesselThresh is None:
            smallVesselThresh = 20
        self.ghostingTab.smallVesselThreshEdit.setText(str(smallVesselThresh))
        
        
        #small vessel exclusion zone
        smallVesselExclX = settings.value("smallVesselExclX")
        if smallVesselExclX is None:
            smallVesselExclX = 3
        self.ghostingTab.smallVesselExclXEdit.setText(str(smallVesselExclX))
        
        smallVesselExclY = settings.value("smallVesselExclY")
        if smallVesselExclY is None:
            smallVesselExclY = 40
        self.ghostingTab.smallVesselExclYEdit.setText(str(smallVesselExclY))
        
        
        #large vessel exclusion zone
        largeVesselExclX = settings.value("largeVesselExclX")
        if largeVesselExclX is None:
            largeVesselExclX = 5
        self.ghostingTab.largeVesselExclXEdit.setText(str(largeVesselExclX))
        
        largeVesselExclY = settings.value("largeVesselExclY")
        if largeVesselExclY is None:
            largeVesselExclY = 70
        self.ghostingTab.largeVesselExclYEdit.setText(str(largeVesselExclY))        
        
        
        #Bright vessel percentile
        brightVesselPerc = settings.value("brightVesselPerc")
        if brightVesselPerc is None:
            brightVesselPerc = 0.997
        self.ghostingTab.brightVesselPercEdit.setText(str(brightVesselPerc)) 
        
        
        #Non Perpendicular settings
        #=============================================
        
        #RemoveNonPerpendicular
        removeNonPerp = settings.value("removeNonPerp")
        if removeNonPerp is None:
            removeNonPerp = True
        else:
            removeNonPerp = removeNonPerp == 'true'
        self.nonPerpTab.removeNonPerpBox.setChecked(removeNonPerp)
        
        #Only MPos
        onlyMPos    = settings.value("onlyMPos")
        if onlyMPos is None:
            onlyMPos = True
        else:
            onlyMPos = onlyMPos == 'true'
        self.nonPerpTab.onlyMPosBox.setChecked(onlyMPos)
        
        #Scaling
        minScaling = settings.value("minScaling")
        if minScaling is None:
            minScaling = 1
        self.nonPerpTab.minScalingEdit.setText(str(minScaling))
        
        maxScaling = settings.value("maxScaling")
        if maxScaling is None:
            maxScaling = 3
        self.nonPerpTab.maxScalingEdit.setText(str(maxScaling))
        
        #Window size
        windowSize = settings.value("windowSize")
        if windowSize is None:
            windowSize = 7
        self.nonPerpTab.windowSizeEdit.setText(
            str(windowSize))
        
        #Magnitude threshold
        magnitudeThresh = settings.value("magnitudeThresh")
        if magnitudeThresh is None:
            magnitudeThresh = 0.8
        self.nonPerpTab.magnitudeThreshEdit.setText(
            str(magnitudeThresh))
        
        #Ratio threshold
        ratioThresh = settings.value("ratioThresh")
        if ratioThresh is None:
            ratioThresh = 2
        self.nonPerpTab.ratioThreshEdit.setText(
            str(ratioThresh))
        
        
        #Deduplicate vessels
        #=============================================
        
        #Deduplicate
        deduplicate = settings.value("deduplicate")
        if deduplicate is None:
            deduplicate = True
        else:
            deduplicate = deduplicate == 'true'
        self.deduplicateTab.deduplicateBox.setChecked(deduplicate)
        
        #Only MPos
        deduplicateRange    = settings.value("deduplicateRange")
        if deduplicateRange is None:
            deduplicateRange = 6
        self.deduplicateTab.deduplicateRangeEdit.setText(
            str(deduplicateRange))
        
        
        #Segmentation settings
        #=============================================
        
        #Brain tissue probability
        whiteMatterProb = settings.value("whiteMatterProb")
        if whiteMatterProb is None:
            whiteMatterProb = 0.5
        self.segmentTab.whiteMatterProb.setText(str(whiteMatterProb))
        
        
        #Clustering settings
        #=============================================
        
        # #Include clusters of significant flow with positive magnitude
        # PositiveMagnitude       = settings.value("PositiveMagnitude")
        # if PositiveMagnitude is None:
        #     PositiveMagnitude   = False
        # else:
        #     PositiveMagnitude   = PositiveMagnitude == 'true'
        # self.clusteringTab.PositiveMagnitudeBox.setChecked(PositiveMagnitude)
        
        # #Include clusters of significant flow with negative magnitude
        # NegativeMagnitude       = settings.value("NegativeMagnitude")
        # if NegativeMagnitude is None:
        #     NegativeMagnitude   = False
        # else:
        #     NegativeMagnitude   = NegativeMagnitude == 'true'
        # self.clusteringTab.NegativeMagnitudeBox.setChecked(NegativeMagnitude)
        
        # #Include clusters of significant flow with isointense magnitude
        # IsointenseMagnitude       = settings.value("IsointenseMagnitude")
        # if IsointenseMagnitude is None:
        #     IsointenseMagnitude   = False
        # else:
        #     IsointenseMagnitude   = IsointenseMagnitude == 'true'
        # self.clusteringTab.IsointenseMagnitudeBox.setChecked(
        #     IsointenseMagnitude)
        
        # #Include clusters of significant flow with positive direction
        # PositiveFlow       = settings.value("PositiveFlow")
        # if PositiveFlow is None:
        #     PositiveFlow   = False
        # else:
        #     PositiveFlow   = PositiveFlow == 'true'
        # self.clusteringTab.PositiveFlowBox.setChecked(PositiveFlow)
        
        # #Include clusters of significant flow with negative direction
        # NegativeFlow       = settings.value("NegativeFlow")
        # if NegativeFlow is None:
        #     NegativeFlow   = False
        # else:
        #     NegativeFlow   = NegativeFlow == 'true'
        # self.clusteringTab.NegativeFlowBox.setChecked(NegativeFlow)
        

    def okButtonPushed(self):
        self.applySettings()
        self.close()        
        
    def applySettings(self):
        """First checks if all entered values are correct, then saves all
        values to the QSettings associated with the program."""
        
        COMPANY = "UMCu"
        APPNAME = "SELMA"
        
        settings = QtCore.QSettings(COMPANY, APPNAME)
        
        #General settings
        #=========================================
        
        #median diameter
        
        medDiam = self.mainTab.medDiamEdit.text()
        try: 
            medDiam = int(medDiam)
        except:
            self.errorLabel.setText(
                    "Median filter diameter has to be an integer.")
            return
        
        if medDiam %2 == 0 and not self.mainTab.mmPixelBox.isChecked():
            self.errorLabel.setText(
                "Median filter diameter has to be an odd number of pixels.")
            return
        
        
        #Pixel or mm diameter:
        mmPixel     = self.mainTab.mmPixelBox.isChecked()      
        
        
        # Confidence interval

        
        confidenceInter = self.mainTab.confidenceInterEdit.text()
        try: 
            confidenceInter = float(confidenceInter)
        except:
            self.errorLabel.setText(
                    "Confidence interval has to be a number.")
            return
        
        if confidenceInter <= 0 or confidenceInter >=1:
            self.errorLabel.setText(
                    "Confidence interval has to be between 0 and 1.")
            return
        
        
        # White matter probability
#        whiteMatterProb = self.mainTab.whiteMatterProbEdit.text()
#        try: 
#            whiteMatterProb = float(whiteMatterProb)
#        except:
#            self.errorLabel.setText(
#                    "White matter probabilty has to be a number.")
#            return
#        
#        if whiteMatterProb < 0 or whiteMatterProb > 1:
#            self.errorLabel.setText(
#                    "White matter probability has to be between 0 and 1.")
#            return        
        
        
        # Average over cycle
        mmVenc              = self.mainTab.mmVencBox.isChecked()
        gaussianSmoothing   = self.mainTab.gaussianSmoothingBox.isChecked()
        ignoreOuterBand     = self.mainTab.ignoreOuterBandBox.isChecked()
        decimalComma        = self.mainTab.decimalCommaBox.isChecked()
        
        # Manual selection
        manualSelection        = self.mainTab.manualSelectionBox.isChecked()
        
        #=========================================
        #=========================================
        #           Structure settings
        #=========================================
        #=========================================
        
        # BasalGanglia   = self.structureTab.BasalGangliaButton.isChecked()
        # SemiovalCentre   = self.structureTab.SemiovalCentreButton.isChecked()
        # AdvancedClustering   = \
        #     self.structureTab.AdvancedClusteringButton.isChecked()
        
        #=========================================
        #=========================================
        #           Ghosting settings
        #=========================================
        #=========================================
        #perform the ghosting filter
        doGhosting = self.ghostingTab.doGhostingBox.isChecked()
        
        #No Vessel threshold
        noVesselThresh = self.ghostingTab.noVesselThreshEdit.text()
        try: 
            noVesselThresh = int(noVesselThresh)
        except:
            self.errorLabel.setText(
                    "No vessel threshold has to be a number.")
            return
        if noVesselThresh < 0:
            self.errorLabel.setText(
                    "No vessel threshold has to be > 0")
            return        
        
        #
        #small Vessel threshold
        smallVesselThresh = self.ghostingTab.smallVesselThreshEdit.text()
        try: 
            smallVesselThresh = int(smallVesselThresh)
        except:
            self.errorLabel.setText(
                    "Small vessel threshold has to be a number.")
            return
        if smallVesselThresh < 0:
            self.errorLabel.setText(
                    "Small vessel threshold has to be > 0.")
            return        
        
        
        #
        #small vessel exclusion zone - X
        smallVesselExclX = self.ghostingTab.smallVesselExclXEdit.text()
        try: 
            smallVesselExclX = int(smallVesselExclX)
        except:
            self.errorLabel.setText(
                    "Small vessel exclusion zone X has to be a number.")
            return
        if smallVesselExclX < 0:
            self.errorLabel.setText(
                    "Small vessel exclusion zone X has to be > 0.")
            return        
        
        #
        #small vessel exclusion zone - Y
        smallVesselExclY = self.ghostingTab.smallVesselExclYEdit.text()
        try: 
            smallVesselExclY = int(smallVesselExclY)
        except:
            self.errorLabel.setText(
                    "Small vessel exclusion zone Y has to be a number.")
            return
        if smallVesselExclY < 0:
            self.errorLabel.setText(
                    "Small vessel exclusion zone Y has to be > 0.")
            return        
        
        #
        #large vessel exclusion zone - X
        largeVesselExclX = self.ghostingTab.largeVesselExclXEdit.text()
        try: 
            largeVesselExclX = int(largeVesselExclX)
        except:
            self.errorLabel.setText(
                    "Large vessel exclusion zone X has to be a number.")
            return
        if largeVesselExclX < 0:
            self.errorLabel.setText(
                    "Large vessel exclusion zone X has to be > 0.")
            return        
        
        #
        #large vessel exclusion zone - Y
        largeVesselExclY = self.ghostingTab.largeVesselExclYEdit.text()
        try: 
            largeVesselExclY = int(largeVesselExclY)
        except:
            self.errorLabel.setText(
                    "Large vessel exclusion zone Y has to be a number.")
            return
        if largeVesselExclY < 0:
            self.errorLabel.setText(
                    "Large vessel exclusion zone Y has to be > 0.")
            return        
        
        #
        #Bright vessel percentile
        brightVesselPerc = self.ghostingTab.brightVesselPercEdit.text()
        try: 
            brightVesselPerc = float(brightVesselPerc)
        except:
            self.errorLabel.setText(
                    "Bright vessel percentile has to be a number.")
            return
        
        if brightVesselPerc < 0 or brightVesselPerc > 1:
            self.errorLabel.setText(
                    "Bright vessel percentile has to between 0 and 1.")
            return        
        

        #=========================================
        #=========================================
        #           Non-Perpendicular
        #=========================================
        #=========================================

        #RemoveNonPerpendicular
        removeNonPerp   = self.nonPerpTab.removeNonPerpBox.isChecked()  
        onlyMPos        = self.nonPerpTab.onlyMPosBox.isChecked()  
        
        #
        #Scaling
        #min
        minScaling = self.nonPerpTab.minScalingEdit.text()
        try: 
            minScaling = float(minScaling)
        except:
            self.errorLabel.setText(
                    "Min. scaling has to be a number.")
            return
        if minScaling < 0:
            self.errorLabel.setText(
                    "Min. scaling has to >0.")
            return     
        #max
        maxScaling = self.nonPerpTab.maxScalingEdit.text()
        try: 
            maxScaling = float(maxScaling)
        except:
            self.errorLabel.setText(
                    "Max. scaling has to be a number.")
            return
        if maxScaling < 0:
            self.errorLabel.setText(
                    "Max. scaling has to > 0.")
            return     
        if maxScaling < minScaling:
            self.errorLabel.setText(
                "Max. scaling has to be larger than Min. scaling.")
            return
        
        #Magnitude Threshold
        windowSize = self.nonPerpTab.windowSizeEdit.text()
        try: 
            windowSize = float(windowSize)
        except:
            self.errorLabel.setText(
                    "Window size has to be a number.")
            return
        if windowSize < 0:
            self.errorLabel.setText(
                    "Window size has to be > 0.")
            return  
        
        
        #Magnitude Threshold
        magnitudeThresh = self.nonPerpTab.magnitudeThreshEdit.text()
        try: 
            magnitudeThresh = float(magnitudeThresh)
        except:
            self.errorLabel.setText(
                    "Magnitude threshold has to be a number.")
            return
        if magnitudeThresh < 0 or magnitudeThresh > 1:
            self.errorLabel.setText(
                    "Magnitude threshold has to be between 0 and 1.")
            return  
        
        
        #Ratio Threshold
        ratioThresh = self.nonPerpTab.ratioThreshEdit.text()
        try: 
            ratioThresh = float(ratioThresh)
        except:
            self.errorLabel.setText(
                "Ratio threshold has to be a number.")
            return
        
        if ratioThresh < 0:
            self.errorLabel.setText(
                "Ratio threshold to be > 0.")
            return   
        
        
       
        #=========================================
        #=========================================
        #           Deduplication
        #=========================================
        #=========================================       
        
        #Deduplicate
        deduplicate   = self.deduplicateTab.deduplicateBox.isChecked()  
        
        #Range
        deduplicateRange = self.deduplicateTab.deduplicateRangeEdit.text()
        try: 
            deduplicateRange = float(deduplicateRange)
        except:
            self.errorLabel.setText(
                "Deduplication range has to be a number.")
            return
        
        if deduplicateRange < 0:
            self.errorLabel.setText(
                "Deduplication range has to be > 0.")
            return  
        
        
        #=========================================
        #=========================================
        #           Segmentation
        #=========================================
        #=========================================       
        
        #
        #Brain mask
        #Prob
        whiteMatterProb = self.segmentTab.whiteMatterProb.text()
        try: 
            whiteMatterProb = float(whiteMatterProb)
        except:
            self.errorLabel.setText(
                    "White matter probability has to be a number.")
            return
        
        if whiteMatterProb < 0 or whiteMatterProb > 1:
            self.errorLabel.setText(
                    "White matter probability has to be between 0 and 1.")
            return 
        
        
        #=========================================
        #=========================================
        #           Clustering settings
        #=========================================
        #=========================================
        
        # PositiveMagnitude   = \
        #     self.clusteringTab.PositiveMagnitudeBox.isChecked()
        # NegativeMagnitude   = \
        #     self.clusteringTab.NegativeMagnitudeBox.isChecked()
        # IsointenseMagnitude = \
        #     self.clusteringTab.IsointenseMagnitudeBox.isChecked()
        # PositiveFlow        = self.clusteringTab.PositiveFlowBox.isChecked()
        # NegativeFlow        = self.clusteringTab.NegativeFlowBox.isChecked()
        
         

        #Save all to settings
        #================================
        #================================
        #Main
        settings.setValue('medDiam',                medDiam)
        settings.setValue('confidenceInter',        confidenceInter)
        settings.setValue('mmPixel',                mmPixel)
#        settings.setValue('whiteMatterProb',        whiteMatterProb)
        settings.setValue('mmVenc',                 mmVenc)
        settings.setValue('gaussianSmoothing',      gaussianSmoothing)
        settings.setValue('ignoreOuterBand',        ignoreOuterBand)
        settings.setValue('decimalComma',           decimalComma)
        settings.setValue('manualSelection',        manualSelection)
        
        #Structure selection
        # settings.setValue('BasalGanglia',           BasalGanglia)
        # settings.setValue('SemiovalCentre',         SemiovalCentre)
        # settings.setValue('AdvancedClustering',     AdvancedClustering)
        
        # settings.setValue('IsointenseMagnitude',    IsointenseMagnitude)
        
        #Ghosting
        settings.setValue('doGhosting',             doGhosting)
        settings.setValue('noVesselThresh',         noVesselThresh)
        settings.setValue('smallVesselThresh',      smallVesselThresh)
        settings.setValue('smallVesselExclX',       smallVesselExclX)
        settings.setValue('smallVesselExclY',       smallVesselExclY)
        settings.setValue('largeVesselExclX',       largeVesselExclX)
        settings.setValue('largeVesselExclY',       largeVesselExclY)
        settings.setValue('brightVesselPerc',       brightVesselPerc)
        
        #nonPerp
        settings.setValue('removeNonPerp',          removeNonPerp)
        settings.setValue('onlyMPos',               onlyMPos)
        settings.setValue('minScaling',             minScaling)
        settings.setValue('maxScaling',             maxScaling)
        settings.setValue('windowSize',             windowSize)
        settings.setValue('magnitudeThresh',        magnitudeThresh)
        settings.setValue('ratioThresh',            ratioThresh)
        
        #Deduplicate
        settings.setValue('deduplicate',            deduplicate)
        settings.setValue('deduplicateRange',       deduplicateRange)
        
        #Segmentation
        settings.setValue('whiteMatterProb',        whiteMatterProb)
        
        #Clustering
        # settings.setValue('PositiveMagnitude',      PositiveMagnitude)
        # settings.setValue('NegativeMagnitude',      NegativeMagnitude)
        # settings.setValue('IsointenseMagnitude',    IsointenseMagnitude)
        # settings.setValue('PositiveFlow',           PositiveFlow)
        # settings.setValue('NegativeFlow',           NegativeFlow)

        #Send signals
        self.thresholdSignal.emit()
        
        
    def reset(self):
        """Removes all settings from the UI, and saves it to the application,
        prompting the values to reset to their defaults.
        """
        COMPANY = "UMCu"
        APPNAME = "SELMA"
        
        settings = QtCore.QSettings(COMPANY, APPNAME)
        settings.clear()
        
        settings.setValue('BasalGanglia',          'false')
        settings.setValue('SemiovalCentre',        'false')
        settings.setValue('MiddleCerebralArtery',  'false')
        settings.setValue('AdvancedClustering',    'false')
        
        settings.setValue('PositiveMagnitude',     'false') 
        settings.setValue('NegativeMagnitude',     'false') 
        settings.setValue('IsointenseMagnitude',   'false') 
        settings.setValue('PositiveFlow',          'false') 
        settings.setValue('NegativeFlow',          'false')
        
        settings.sync()
        
        self.getSettings()




# ====================================================================