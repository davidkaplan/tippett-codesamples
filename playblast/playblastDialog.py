#*******************************************************************************
# Copyright (c) 2007 Tippett Studio. All rights reserved.
# $Id$ 
#*******************************************************************************

import os
import sys
from PyQt4 import Qt, QtCore, QtGui, uic
import shutil

import tip.db.studio2
from tip.gtoCache.podFarmJob import TEMP_POD_SPOOL_DIR
import tip.maya.playblast.playblast
from tip.utils.TemplateConfigParser import TemplateConfigParser
    
__dialogs = list()

CONFIG_DEFAULTS = dict()
CONFIG_DEFAULTS['format'] = 'tif'
CONFIG_DEFAULTS['outputDir'] = '/tmp'
CONFIG_DEFAULTS['width'] = 1024
CONFIG_DEFAULTS['height'] = 768
CONFIG_DEFAULTS['viewerArgs'] = ''
CONFIG_DEFAULTS['viewer'] = 'rv'
CONFIG_DEFAULTS['playblastOffscreen'] = True
CONFIG_DEFAULTS['viewImmediately'] = True

PRESET_DEST_PATHS = ['/tip', '/tip/volatile', '/show']
AVAILABLE_PLAYERS = ['rv', 'flipper', 'fcheck']

CONFIG_OPTIONS = ['format', 'width', 'height']

# This is dumb.  Is there a better way? sys.maxint doesn't play well with qt.
MAX_INT = 2**31-1


def getResolutions(show=None):
    '''
    A helper method to get the list of available resolutions for a show from the imageRes table.
    '''
    if not show:
        show = os.getenv('TS_SHOW')
    if show:
        dbh = tip.db.studio2.connectStudio()
        showResolutions = tip.db.studio2.selectShowResolutions(dbh, show)
        if showResolutions:
            return showResolutions
    return list()


class InputResolutionDialog(QtGui.QDialog):
    '''
    A helper dialog to let users enter custom resolutions through spinboxes.
    '''
    def __init__(self, width, height):
        super(QtGui.QDialog, self).__init__()
        self.setWindowTitle("Tippett Playblast Options")
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)    
        self.spinnersLayout = QtGui.QHBoxLayout()
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.widthSpinbox = QtGui.QSpinBox()
        self.widthSpinbox.setRange(1, MAX_INT)
        self.widthSpinbox.setValue(width)
        self.heightSpinbox = QtGui.QSpinBox()
        self.heightSpinbox.setRange(1, MAX_INT)
        self.heightSpinbox.setValue(height)        
        self.spinnersLayout.addWidget(QtGui.QLabel('Width: '))
        self.spinnersLayout.addWidget(self.widthSpinbox)
        self.spinnersLayout.addWidget(QtGui.QLabel('Height: '))
        self.spinnersLayout.addWidget(self.heightSpinbox)
        self.okButton = QtGui.QPushButton('Okay')
        self.cancelButton = QtGui.QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.buttonsLayout.addWidget(self.okButton)
        self.buttonsLayout.addWidget(self.cancelButton)
        self.layout.addLayout(self.spinnersLayout)
        self.layout.addLayout(self.buttonsLayout)
        
    def getResolution(self):
        return (self.widthSpinbox.value(), self.heightSpinbox.value())



class TipPlayblastSettingsWidget(QtGui.QDialog):
    '''
    The main widget.  This holds all of the UI items that directly affect playblast settings.
    '''

    def __init__(self, start=1001, end=1010):
        '''
        '''
        super(QtGui.QDialog, self).__init__()

        # Config vars
        self.format = CONFIG_DEFAULTS['format']
        self.filename = ''
        self.outputDir = CONFIG_DEFAULTS['outputDir']
        self.width = CONFIG_DEFAULTS['width']
        self.height = CONFIG_DEFAULTS['height']
        self.onFarm = False
        self.viewerArgs = CONFIG_DEFAULTS['viewerArgs']
        self.viewer = CONFIG_DEFAULTS['viewer']
        self.playblastOffscreen = CONFIG_DEFAULTS['playblastOffscreen']
        self.viewImmediately = CONFIG_DEFAULTS['viewImmediately']
        
        # Other constant vars
        self.presetPaths = PRESET_DEST_PATHS
        self.availableViewers = AVAILABLE_PLAYERS
        
        # Framerange vars
        self.start = start
        self.end = end
        
        # Image extension vars
        self.availableFormats = tip.maya.playblast.playblast.IMAGE_FORMAT_DICT.keys()
        self.availableFormats.sort()

        # Create the dialog
        self.setWindowTitle("Tippett Playblast Options")
        self.uiSettings = QtCore.QSettings("Tippett Studio", "MayaPlayblast")
        
        # The master layout
        self.layout = QtGui.QFormLayout()
        self.setLayout(self.layout)
        
        # Playblast base filename
        try:
            self.filename = os.path.splitext(os.path.basename(tip.maya.playblast.playblast.scenePath()))[0]
        except Exception, e:
            print e        
        self.filenameLineEdit = QtGui.QLineEdit(self.filename)
        self.layout.addRow('Filename', self.filenameLineEdit)

        # Playblast path, and a nifty system file browser
        self.fileBrowserLineEdit = QtGui.QLineEdit()
        self.fileBrowseButton = QtGui.QToolButton()
        self.icon = QtGui.QApplication.style().standardIcon(QtGui.QStyle.StandardPixmap(QtGui.QStyle.SP_DialogOpenButton))
        self.fileBrowseButton.setIcon(self.icon)
        self.fileLayout = QtGui.QHBoxLayout()
        self.fileLayout.addWidget(self.fileBrowserLineEdit)
        self.fileLayout.addWidget(self.fileBrowseButton)
        self.layout.addRow('Directory', self.fileLayout)
        self.fileBrowseButton.clicked.connect(self.slotFileBrowseClicked)

        # Time spinboxes
        try:
            self.start, self.end = tip.maya.playblast.playblast.getTimeSlider()
        except Exception, e:
            print e
        self.timeLayout = QtGui.QHBoxLayout()
        self.startSpinBox = QtGui.QSpinBox()
        self.endSpinBox = QtGui.QSpinBox()
        self.startSpinBox.setRange(1, MAX_INT)  # sys.maxint and sys.maxsize don't work
        self.endSpinBox.setRange(1, MAX_INT)
        self.startSpinBox.setValue(self.start)
        self.endSpinBox.setValue(self.end)
        self.startSpinBox.setFixedWidth(70)
        self.endSpinBox.setFixedWidth(70)
        self.timeLayout.addWidget(self.startSpinBox)
        self.timeLayout.addWidget(QtGui.QLabel('  End Frame'))
        self.timeLayout.addWidget(self.endSpinBox)
        self.layout.addRow('Start Frame', self.timeLayout)
        
        # Image format drop down 
        self.formatComboBox = QtGui.QComboBox()
        for ext in self.availableFormats:
            self.formatComboBox.addItem(ext)
        self.layout.addRow('Format', self.formatComboBox)

        # Resolution drop down with a nifty method for adding custom resolutions
        self.resComboBox = QtGui.QComboBox()
        resolutions = getResolutions()
        for res in resolutions:
            size = QtCore.QVariant(QtCore.QSize(int(res['width']), int(res['height'])))
            self.resComboBox.addItem('%s x %s' % (size.toSize().width(), size.toSize().height()), size) 
        self.resComboBox.addItem('Custom...')
        self.layout.addRow('Resolution', self.resComboBox)
        self.resComboBox.currentIndexChanged.connect(self.slotResComboIndexChanged)
        self.currentResComboBoxIndex = self.resComboBox.currentIndex()
        
        # A nice horizontal line spacer
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        self.layout.addRow(line)
 
        # Toggle local or farm playblasting
        self.farmLayout = QtGui.QHBoxLayout()
        self.localRadioButton = QtGui.QRadioButton('Locally')
        self.farmRadioButton = QtGui.QRadioButton('On Farm')
        self.localRadioButton.setChecked(True)
        self.farmLayout.addWidget(self.localRadioButton)
        self.farmLayout.addWidget(self.farmRadioButton)
        self.layout.addRow('Perform playblast: ', self.farmLayout)
        self.localRadioButton.toggled.connect(self.slotFarmOptionChanged)
        self.farmRadioButton.toggled.connect(self.slotFarmOptionChanged)
                
        # Offscreen or not
        self.offscreenCheckbox = QtGui.QCheckBox()
        self.layout.addRow('Playblast Offscreen', self.offscreenCheckbox)
        self.offscreenCheckbox.stateChanged.connect(self.slotOffscreenCheckboxChanged)
        
        # View immediately, and select viewer
        self.immediatelyCheckbox = QtGui.QCheckBox()
        self.viewerComboBox = QtGui.QComboBox()
        for player in self.availableViewers:
            self.viewerComboBox.addItem(player)
        self.viewerLayout = QtGui.QHBoxLayout()
        self.viewerLayout.addWidget(self.immediatelyCheckbox)
        self.viewerLayout.addWidget(QtGui.QLabel('Viewer:'))
        self.viewerLayout.addWidget(self.viewerComboBox)
        self.layout.addRow('View Immediately', self.viewerLayout)
        self.immediatelyCheckbox.stateChanged.connect(self.slotViewImmediatelyChanged)
        self.slotViewImmediatelyChanged()
        
        # Additional viewer args
        self.viewerArgsLineEdit = QtGui.QLineEdit()
        self.viewerArgsLineEdit.setReadOnly(True)
        #self.viewerArgsLineEdit.setStyleSheet("background:transparent;")  
        self.editViewerArgsPushButton = QtGui.QPushButton('Edit')
        self.viewerArgsLayout = QtGui.QHBoxLayout()
        self.viewerArgsLayout.addWidget(self.viewerArgsLineEdit)
        self.viewerArgsLayout.addWidget(self.editViewerArgsPushButton)
        self.editViewerArgsPushButton.clicked.connect(self.slotViewerArgsButtonClicked)
        self.layout.addRow('Additional Viewer Args: ', self.viewerArgsLayout)            

    
    def updateVars(self):
        '''
        Get current values from widgets
        '''
        self.filename = str(self.filenameLineEdit.text())
        self.outputDir = str(self.fileBrowserLineEdit.text())
        self.start = self.startSpinBox.value()
        self.end = self.endSpinBox.value()
        self.format = str(self.formatComboBox.currentText())
        self.width = self.resComboBox.itemData(self.currentResComboBoxIndex).toSize().width()
        self.height = self.resComboBox.itemData(self.currentResComboBoxIndex).toSize().height()
        self.onFarm = self.farmRadioButton.isChecked()
        self.viewer = self.viewerComboBox.currentText()
        self.viewImmediately = self.immediatelyCheckbox.isChecked()
        self.viewerArgs = self.viewerArgsLineEdit.text()
        self.playblastOffscreen = self.offscreenCheckbox.isChecked()        


    def values(self):
        '''
        Return a dict of the UI values.
        '''
        self.updateVars()
        varDict = dict()
        varDict['filename'] = self.filename
        varDict['outputDir'] = self.outputDir
        varDict['format'] = self.format
        varDict['width'] = self.width
        varDict['height'] = self.height
        varDict['onFarm'] = self.onFarm
        varDict['viewer'] = self.viewer
        varDict['viewImmediately'] = self.viewImmediately
        varDict['viewerArgs'] = self.viewerArgs
        varDict['playblastOffscreen'] = self.playblastOffscreen 
        return varDict
             

    def setValues(self, varDict, blockSignals=True):
        '''
        Set UI values given a dict.
        '''    
        # Block Signals
        if blockSignals:
            self.formatComboBox.blockSignals(True)
            self.resComboBox.blockSignals(True)
            self.fileBrowserLineEdit.blockSignals(True)
            self.offscreenCheckbox.blockSignals(True)
            self.farmRadioButton.blockSignals(True)
            self.viewerComboBox.blockSignals(True)
            self.immediatelyCheckbox.blockSignals(True)
            self.viewerArgsLineEdit.blockSignals(True)
        
        # Set the widgets
        if 'format' in varDict:
            if self.formatComboBox.findText(varDict['format']) == -1:
                print 'Warning: Image format %s is invalid.' % varDict['format']
            self.formatComboBox.setCurrentIndex(self.formatComboBox.findText(varDict['format']))      
        # Resolution 
        if 'width' and 'height' in varDict:
            size = QtCore.QVariant(QtCore.QSize(varDict['width'], varDict['height']))
            index = self.resComboBox.findData(size)
            if not index == -1:
                self.resComboBox.setCurrentIndex(index)
            else:
                count = self.resComboBox.count()
                self.resComboBox.insertItem(count-1, '%s x %s' % (size.toSize().width(), size.toSize().height()), size)
                self.resComboBox.setCurrentIndex(count-1) 
        if 'outputDir' in varDict:
            self.fileBrowserLineEdit.setText(varDict['outputDir'])        
        if 'playblastOffscreen' in varDict:
            self.offscreenCheckbox.setChecked(varDict['playblastOffscreen'])
        if 'onFarm' in varDict:
            self.farmRadioButton.setChecked(varDict['onFarm'])
        if 'viewer' in varDict:
            self.viewerComboBox.setCurrentIndex(self.viewerComboBox.findText(varDict['viewer']))
        if 'viewImmediately' in varDict:
            self.immediatelyCheckbox.setChecked(varDict['viewImmediately'])
        if 'viewerArgs' in varDict:
            self.viewerArgsLineEdit.setText(varDict['viewerArgs'])  
        
        # Unblock signals
        if blockSignals:
            self.formatComboBox.blockSignals(False)
            self.resComboBox.blockSignals(False)        
            self.fileBrowserLineEdit.blockSignals(False)
            self.offscreenCheckbox.blockSignals(False)
            self.farmRadioButton.blockSignals(False)
            self.viewerComboBox.blockSignals(False)
            self.immediatelyCheckbox.blockSignals(False)
            self.viewerArgsLineEdit.blockSignals(False)

    
    def doPlayblast(self):
        '''
        Playblast locally, or create and send a job to the farm.
        '''
           
        # Get updated values
        self.updateVars()
        blastpath = os.path.join(self.outputDir, self.filename)
        
        if self.onFarm:
            # If changes, prompt save now
            if tip.maya.playblast.playblast.sceneModified():
                QtGui.QMessageBox.warning(self, 'Unable to Playblast', 'Maya scene has unsaved changes.\nPlease save scene and try again.')
                return
                
            # Check for window focus and get current modelEditor
            ret, panelName = tip.maya.playblast.playblast.getPanel()
            if not ret:
                QtGui.QMessageBox.warning(self, 'Unable to Playblast', 'Invalid active window.\nPlease select a viewport window and try again.')
                return

            try:
                # Copy file to spool
                scene = tip.maya.playblast.playblast.scenePath()
                user = os.getenv('USER', 'nobody')
                basename = os.path.splitext(os.path.basename(scene))
                newname = '%s_%s%s' % (basename[0], user, basename[1])
                newpath = os.path.join(TEMP_POD_SPOOL_DIR, newname)
                shutil.copyfile(scene, newpath)  
                              
                # Submit job
                job = tip.maya.playblast.playblast.playblastFarmJob(newpath, blastpath, format=self.format, width=self.width, 
                                                            height=self.height, start=self.start, end=self.end, panel=panelName)
                job.submit()
                
                QtGui.QMessageBox.information(self, 'Success', 'Job %s sent to farm.' % job.name)
                
            except Exception, e:
                QtGui.QMessageBox.critical(self, 'Unable to Playblast', str(e))
            
        else:
            # Do the playblast locally
            tip.maya.playblast.playblastLocal(blastpath, self.format, self.start, self.end, self.playblastOffscreen, self.width, self.height)
                                                                    
            # Launch the viewer
            if self.viewImmediately:
                tip.maya.playblast.launchViewer(blastpath, self.format, self.start, self.end, self.viewer, self.viewerArgs)

  
    ### DIALOG WINDOWS ###
    
    def slotViewerArgsButtonClicked(self):
        '''
        Set additional viewer args in a modal dialog to make it a bit more formal.
        '''
        origText = self.viewerArgsLineEdit.text()
        text, ok = QtGui.QInputDialog.getText(self, 'Input Text', 'Viewer command line arguments:', QtGui.QLineEdit.Normal, origText)
        if ok:
            self.viewerArgsLineEdit.setText(text)
            

    def slotResComboIndexChanged(self, index):
        '''
        Pop up an InputResolutionDialog when necessary.
        '''
        self.resComboBox.blockSignals(True)
        if self.resComboBox.itemText(index) == 'Custom...':
            width = self.resComboBox.itemData(self.currentResComboBoxIndex).toSize().width()
            height = self.resComboBox.itemData(self.currentResComboBoxIndex).toSize().height()
            dialog = InputResolutionDialog(width, height)
            if dialog.exec_() == QtGui.QDialog.Accepted:
                width, height = dialog.getResolution()
                del(dialog) # necessary?
                size = QtCore.QVariant(QtCore.QSize(width, height))
                index = self.resComboBox.findData(size)
                if not index == -1:
                    self.resComboBox.setCurrentIndex(index)
                else:
                    count = self.resComboBox.count()
                    self.resComboBox.insertItem(count-1, '%s x %s' % (size.toSize().width(), size.toSize().height()), size)
                    self.resComboBox.setCurrentIndex(count-1)
            else:
                self.resComboBox.setCurrentIndex(self.currentResComboBoxIndex)
        self.currentResComboBoxIndex = self.resComboBox.currentIndex()
        self.resComboBox.blockSignals(False)


    def slotFileBrowseClicked(self):
        '''
        Open a file browser window.
        '''
        dialog = QtGui.QFileDialog(self, 'Choose output directory', self.fileBrowserLineEdit.text())   
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True) 
        urls = dialog.sidebarUrls()
        urls += [QtCore.QUrl('file://'+path) for path in self.presetPaths]
        dialog.setSidebarUrls(urls)
        if dialog.exec_():
            self.fileBrowserLineEdit.setText(dialog.selectedFiles()[0])
   
    ### CHECKBOXES ###
   
    def slotFarmOptionChanged(self):
        if self.farmRadioButton.isChecked():
            self.offscreenCheckbox.setEnabled(False)
            self.immediatelyCheckbox.setEnabled(False)
            self.viewerComboBox.setEnabled(False)
            self.resComboBox.setEnabled(True)
        else:
            self.offscreenCheckbox.setEnabled(True)
            self.immediatelyCheckbox.setEnabled(True)
            self.viewerComboBox.setEnabled(True)         
        self.slotOffscreenCheckboxChanged()
        self.slotViewImmediatelyChanged()   

    def slotOffscreenCheckboxChanged(self):
        if self.offscreenCheckbox.isEnabled():
            if self.offscreenCheckbox.isChecked():
                self.resComboBox.setEnabled(True)
            else:
                self.resComboBox.setEnabled(False)            
    
    def slotViewImmediatelyChanged(self):
        if self.immediatelyCheckbox.isEnabled():
            if self.immediatelyCheckbox.isChecked():
                self.viewerComboBox.setEnabled(True)
            else:
                self.viewerComboBox.setEnabled(False)


def sanitizeConfigOptions(options):
    '''
    A helper method to convert the values of an option dict to strings for input to a TemplateConfigParser.
    Mostly this exists to convert pythons True/False bools to a ConfigParser INI's 'yes'/'no' string requirement.
    '''
    retDict = dict()
    for key, value in options.items():
        if isinstance(value, bool):
            if value:
                value = 'yes'
            else:
                value = 'no'
        retDict[key] = str(value)
    return retDict
    

class TipPlayblastDialog(QtGui.QDialog):
    """
    The dialog window that holds the settings widget.  This dialog handles the config presets.
    """

    def __init__(self, start=1001, end=1010):
        """
        """
        super(QtGui.QDialog, self).__init__()

        # Read the config
        studioConfigFilename = os.path.expandvars("$TIP_APPS_ROOT/$TIP_APPS_DEPOT/etc/maya/playblast.ini")
        showConfigFilename = os.path.expandvars("$TIP_SHOW_ROOT/$TS_SHOW/etc/maya/playblast.ini")
        self.configFile = TemplateConfigParser(sanitizeConfigOptions(CONFIG_DEFAULTS))
        self.configFile.read([studioConfigFilename, showConfigFilename])
        
        # Create the dialog
        self.setWindowTitle("Tippett Playblast Options")
        self.uiSettings = QtCore.QSettings("Tippett Studio", "MayaPlayblast")
        
        # The master layout
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
    
        # The config settings combo box
        self.configPresetComboBox = QtGui.QComboBox()
        orderedSections = self.configFile.sections()
        orderedSections.sort()
        for section in orderedSections:
            self.configPresetComboBox.addItem(section)
        self.configPresetComboBox.addItem("User Settings")
        self.configPresetComboBox.setCurrentIndex(self.configPresetComboBox.count()-1)
        self.configPresetComboBox.currentIndexChanged.connect(self.slotConfigPresetComboChanged)
        self.layout.addWidget(self.configPresetComboBox)
        self.configCurrentText = str(self.configPresetComboBox.currentText())

        # The main settings widget
        self.playblastSettings = TipPlayblastSettingsWidget()
        # Put a box around it.
        self.boxLayout = QtGui.QGroupBox()
        self.boxLayout.setLayout(self.playblastSettings.layout)
        self.layout.addWidget(self.boxLayout)
        
        # Update presets when values are changed
        self.playblastSettings.formatComboBox.currentIndexChanged.connect(self.slotUpdateConfig)
        self.playblastSettings.resComboBox.currentIndexChanged.connect(self.slotUpdateConfig)
        self.playblastSettings.viewerComboBox.currentIndexChanged.connect(self.slotUpdateConfig)
        self.playblastSettings.viewerArgsLineEdit.textChanged.connect(self.slotUpdateConfig)

        # Our bottom row buttons for doing stuff
        self.playblastButton = QtGui.QPushButton('Playblast')
        self.applyButton = QtGui.QPushButton('Apply')
        self.closeButton = QtGui.QPushButton('Close')
        self.closeButton.setDefault(True)
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.buttonsLayout.addWidget(self.playblastButton)
        self.buttonsLayout.addWidget(self.applyButton)
        self.buttonsLayout.addWidget(self.closeButton)
        self.layout.addLayout(self.buttonsLayout) 
        self.playblastButton.clicked.connect(self.slotPlayblastPushed)
        self.applyButton.clicked.connect(self.slotApplyPushed)
        self.closeButton.clicked.connect(self.slotClosePushed)        
        self.playblastSettings.localRadioButton.toggled.connect(self.slotSettingsFarmOptionChanged)
  
        # Set initial values
        self.playblastSettings.setValues(self.varsFromConfig())
        
        # Now remove defaults so we only get the values specified in the ini sections
        self.configFile._defaults = {}
        
        # Store settings
        self.userSettings = self.playblastSettings.values()


    def varsFromConfig(self, section='DEFAULT'):
        '''
        Return a dict of settings from a specific section in the config.
        '''
        varDict = dict()
        if self.configFile.has_option(section, 'format'):
            varDict['format'] = self.configFile.get(section, 'format')
        if self.configFile.has_option(section, 'outputDir'):
            varDict['outputDir'] = self.configFile.get(section, 'outputDir')
        if self.configFile.has_option(section, 'width'):
            varDict['width'] = self.configFile.getint(section, 'width')
        if self.configFile.has_option(section, 'height'):
            varDict['height'] = self.configFile.getint(section, 'height')
        if self.configFile.has_option(section, 'onFarm'):
            varDict['onFarm'] = self.configFile.get(section, 'onFarm')                        
        if self.configFile.has_option(section, 'viewerArgs'):
            varDict['viewerArgs'] = self.configFile.get(section, 'viewerArgs')
        if self.configFile.has_option(section, 'viewer'):
            varDict['viewer'] = self.configFile.get(section, 'viewer')
        if self.configFile.has_option(section, 'playblastOffscreen'):
            varDict['playblastOffscreen'] = self.configFile.getboolean(section, 'playblastOffscreen')
        if self.configFile.has_option(section, 'viewImmediately'):
            varDict['viewImmediately'] = self.configFile.getboolean(section, 'viewImmediately')      
        return varDict
    
    
    def slotConfigPresetComboChanged(self):
        '''
        Set UI values to selected config section, or revert to previous user values.
        '''
        # If changing away from 'user settings', save the current settings to be restored later.
        if self.configCurrentText == 'User Settings':
            self.userSettings = self.playblastSettings.values()
            
        # Set current config for test against again later
        self.configCurrentText = str(self.configPresetComboBox.currentText())
            
        # Get the selected settings
        settingsToCopy = dict()
        if self.configCurrentText == 'User Settings':
            settingsToCopy = self.userSettings
        else:
            settingsToCopy = self.varsFromConfig(self.configCurrentText)
            self.playblastSettings.setValues(self.varsFromConfig(self.configCurrentText))   
        
        # Copy only the options we want
        for key, value in settingsToCopy.items():
            if key not in CONFIG_OPTIONS:
                del settingsToCopy[key]
                
        # Set the widget values
        self.playblastSettings.setValues(settingsToCopy)


    def compareSettings(self, section):
        '''
        A helper method to determine if current settings equal a preset.
        '''
        currentSettings = self.playblastSettings.values()
        configSettings = self.varsFromConfig(section)
        isPreset = True
        for option in currentSettings:
            if option in CONFIG_OPTIONS:
                if not currentSettings[option] == configSettings[option]:
                    isPreset = False
                    break        
        return isPreset
        

    def slotUpdateConfig(self):
        '''
        When a UI widget is changed, set the preset to 'user settings' unless it equals an existing preset.
        '''
        # Get current values
        currentSettings = self.playblastSettings.values()
        
        # Check if user settings are a preset
        if self.configPresetComboBox.currentText() == 'User Settings':
            for section in self.configFile.sections():
                if self.compareSettings(section):
                    self.configPresetComboBox.setCurrentIndex(self.configPresetComboBox.findText(section))  
                    break
        # Otherwise, set to 'user settings' if the current values do not equal the selected preset.
        else:
            if not self.compareSettings(self.configCurrentText):
                self.userSettings = self.playblastSettings.values()
                self.configPresetComboBox.setCurrentIndex(self.configPresetComboBox.findText('User Settings'))                 


    def slotSettingsFarmOptionChanged(self):
        '''
        Rename the text on the playblast button if sending to the farm.
        '''
        if self.playblastSettings.farmRadioButton.isChecked():
            self.playblastButton.setText('Submit Job')
        else:       
            self.playblastButton.setText('Playblast')       
     
             
    ### BUTTONS ###

    def slotPlayblastPushed(self):
        """
        Run the playblast, and close the window.
        """
        self.playblastSettings.doPlayblast()
        
        self.close()


    def slotApplyPushed(self):
        """
        Save preferences, run the playblast, and don't close the window.
        """
        self.playblastSettings.doPlayblast()
        self.raise_()        # Necessary since Maya brings its main window forward upon onscreen playblast


    def slotClosePushed(self):
        """
        Don't save preferences, don't run the playblast, and close the window.
        """
        self.close()
    
    
    ### OPEN AND CLOSE ###  
    
    @staticmethod
    def getUISettings():
        '''
        A helper method to get saved ui settings by converting QVariant objects to python objects.
        '''
        # Get saved preferences
        returnDict = dict()
        uiSettings = QtCore.QSettings("Tippett Studio", "MayaPlayblast")
        uiSettings.beginGroup('UserSettings')
        qsettings = uiSettings.value("userSettings", QtCore.QVariant(dict())).toPyObject()
        preset = uiSettings.value("preset").toString()
        uiSettings.endGroup()
        for qkey, qvalue in qsettings.items():
            key = str(qkey)
            if key in ['height', 'width']:
                returnDict[key] = qvalue.toInt()[0] # why does it return a tuple? i don't know.
            elif key in ['onFarm', 'playblastOffscreen', 'viewImmediately']:
                returnDict[key] = qvalue.toBool() 
            elif key in ['filename', 'format', 'outputDir', 'viewer', 'viewerArgs']:
                returnDict[key] = str(qvalue.toString())
            else:
                raise RuntimeError, 'Unrecognized option: %s' % key                    
        return returnDict, preset


    def showEvent(self, event):
        """
        """
        # Set window settings
        if event.spontaneous():
            return
        defaultSize = QtCore.QSize(492, 330)
        defaultPos = QtCore.QPoint(200, 300)
        self.uiSettings.beginGroup("MainWindow")
        self.resize(self.uiSettings.value("size", QtCore.QVariant(defaultSize)).toSize())
        self.move(self.uiSettings.value("pos", QtCore.QVariant(defaultPos)).toPoint())
        self.uiSettings.endGroup()
        
        # Set user preferences     
        self.userSettings, preset = self.getUISettings()
        self.configPresetComboBox.setCurrentIndex(self.configPresetComboBox.findText('User Settings'))
        self.playblastSettings.setValues(self.userSettings, blockSignals=False)
        if not self.configPresetComboBox.findText(preset) == -1:
            self.configPresetComboBox.setCurrentIndex(self.configPresetComboBox.findText(preset))
        self.playblastSettings.slotFarmOptionChanged()               


    def closeEvent(self, event):
        """
        """
        # Save window settings
        self.uiSettings.beginGroup("MainWindow")
        self.uiSettings.setValue("size", QtCore.QVariant(self.size()))
        self.uiSettings.setValue("pos", QtCore.QVariant(self.pos()))
        self.uiSettings.endGroup()
        
        # Save user preferences
        qVarDict = dict()
        self.userSettings = self.playblastSettings.values()
        for key, value in self.userSettings.items():
            qVarDict[QtCore.QString(key)] = QtCore.QVariant(value)
        self.uiSettings.beginGroup("UserSettings")
        self.uiSettings.setValue("userSettings", QtCore.QVariant(qVarDict))
        self.uiSettings.setValue("preset", QtCore.QVariant(self.configCurrentText))
        self.uiSettings.endGroup()
        self.done(0)


################################################################################

def doTipPlayblastImmediately():
    """
    Do a local playblast without launching the UI, using the last saved settings.
    """
    varDict = CONFIG_DEFAULTS
    varDict.update(TipPlayblastDialog.getUISettings()[0])
    blastpath = os.path.join(varDict['outputDir'], varDict['filename'])
    start, end = tip.maya.playblast.playblast.getTimeSlider()
    tip.maya.playblast.playblast.playblastLocal(blastpath, varDict['format'], start, end, varDict['playblastOffscreen'], varDict['width'], varDict['height'])
    if varDict['viewImmediately']:
        tip.maya.playblast.launchViewer(blastpath, varDict['format'], start, end, varDict['viewer'], varDict['viewerArgs'])


def launchTipPlayblastSettings():
    """
    """
    global __dialogs
    dialog = TipPlayblastDialog()
    dialog.show()
    __dialogs.append(dialog)


# Test Harness
if __name__ == '__main__':
    import sys
    QtGui.QApplication.setDesktopSettingsAware(False)
    app = QtGui.QApplication(sys.argv)
    launchTipPlayblastSettings()
    sys.exit(app.exec_())

#     doTipPlayblastImmediately()
