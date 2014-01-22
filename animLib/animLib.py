#!/usr/bin/env python
#*******************************************************************************
# Copyright (c) 2012 Tippett Studio. All rights reserved.
# $Id$ 
#*******************************************************************************
"""
This will create a TipGtoViz for published animations in the animlib sequence, and allow for repositioning and name changes.
Then, it will allow for publishing a pod with a renamed character, for rendering by TD
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic

from tip.db.asset import *
from tip.db.studio import *

from tip.gtoCache.podCache import GtoGeometryCachePod

import pymel.core as pm

import tempfile
import os

import animLibFarmJob
import bdNamingConventions

#### If this were a more permanent tool, there should be more consistency in how attributes are set and gotten from objects

NAMES_INFO = bdNamingConventions.NAMES_INFO

#### Read the UI from the same directory as the python module
modPath = os.path.realpath(__file__)
uiDir = QDir().setCurrent(os.path.dirname(modPath))

form_class, base_class = uic.loadUiType('animLib.ui')
class AnimLibWindow(base_class, form_class):
    def __init__(self, parent=None):
        super(base_class, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName('animLibPublish')
        self.setWindowTitle("Animation Lib Publish")

        self.wolfList = bdNamingConventions.WOLF_LIST
        self.vampList = bdNamingConventions.VAMP_LIST
                
        self.selVizNode = None

        self.addLibActions()
        self.addLibChars()
        
        self.populateSeq()

        self.scriptJobID = pm.scriptJob(e=["SelectionChanged", updateWindow], kws=True)  
        
        self.settings = QSettings("Tippett Studio", "AnimLib")       
        
    def showEvent(self, event):
        if event.spontaneous():
            return
        defaultPos = QPoint(200, 300)
        self.settings.beginGroup("MainWindow")
        animLibSeq = self.settings.value("libSeq", QVariant(self.animLibComboBox.currentText())).toString()
        pubSeq = self.settings.value("pubSeq", QVariant(self.seqComboBox.currentText())).toString()
        pubShot = self.settings.value("pubShot", QVariant(self.shotComboBox.currentText())).toString()
        self.animLibComboBox.setCurrentIndex(self.animLibComboBox.findText(animLibSeq))
        self.seqComboBox.setCurrentIndex(self.seqComboBox.findText(pubSeq))
        self.shotComboBox.setCurrentIndex(self.shotComboBox.findText(pubShot))
        self.move(self.settings.value("pos", QVariant(defaultPos)).toPoint())
        self.settings.endGroup()
                
    def closeEvent(self, event):
        pm.scriptJob(kill=self.scriptJobID)
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("libSeq", QVariant(self.animLibComboBox.currentText()))
        self.settings.setValue("pubSeq", QVariant(self.seqComboBox.currentText()))
        self.settings.setValue("pubShot", QVariant(self.shotComboBox.currentText()))
        self.settings.setValue("pos", QVariant(self.pos()))
        self.settings.endGroup()
        
    #### Get the list of actions from Shotgun and populate the dropdown     
    def addLibActions(self):
        libShots = Shot.selectBy(production='bd', sequence='animlib')
        for shot in libShots:
            self.animLibComboBox.addItem(shot.name[8:])

    #### Find what has been published for each seq and add it to the dropdown
    def addLibChars(self):
        podPublishes = list(getElements('bd', 'animlib1%s'%self.animLibComboBox.currentText(), assetType='geometryCache'))
        podPublishes.sort()
        self.characterComboBox.clear()
        self.characterComboBox.addItems(list(podPublishes))

    #### Populate the options combo box for 'publish as' possibilities            
    def populateOutputs(self):
        self.publishAsComboBox.blockSignals(True)
        self.publishAsComboBox.clear()
                        
        if not self.selVizNode:
            return

        origName = pm.getAttr('%s.originalName'%self.selVizNode)      
        creature = bdNamingConventions.getCharacterFromFullname(origName)
   
        if creature in self.vampList:
            vampList = [NAMES_INFO[char]['fullname'] for char in self.vampList]
            vampList.sort()
            self.publishAsComboBox.addItems(vampList)   
        elif creature in self.wolfList and 'young' in creature:
            wolfList = [NAMES_INFO[char]['fullname'] for char in self.wolfList if 'young' in char]                     
            wolfList.sort()
            self.publishAsComboBox.addItems(wolfList) 
        elif creature in self.wolfList and 'young' not in creature:
            wolfList = [NAMES_INFO[char]['fullname'] for char in self.wolfList if 'young' not in char]                     
            wolfList.sort()
            self.publishAsComboBox.addItems(wolfList)
        else:
            pm.warning('Creature name %s not recognized' % creature)
            
        self.publishAsComboBox.blockSignals(False)    
        

    #### Populate the possible sequences for publishing into
    def populateSeq(self):
        seqs = Sequence.selectBy(production='bd')
        for s in seqs:
            self.seqComboBox.addItem(s.name)
    
    #### Read values from the pod and feed that to the gtoViz
    def getPodPath(self):
        curShot = 'animlib1%s'%self.animLibComboBox.currentText()
        curChar = str(self.characterComboBox.currentText())
        curVersion = getLatestVersion('bd', curShot, 'geometryCache', curChar, fileFormat='pod')
        curPath = getAssetPath('bd', curShot, 'geometryCache', curChar, version=curVersion, fileFormat='pod')
        return curPath


    #### Create the GtoViz and add attributes to track what it originally was
    def createGtoViz(self, podPath):

        ggcp = GtoGeometryCachePod.fromPodFile(podPath)
        startFrame = ggcp.startFrame
        endFrame = ggcp.endFrame
        cacheFilename = ggcp.cacheFilename

        pm.loadPlugin('TipGtoView', qt=True)
        gtoViz = pm.createNode('TipGtoView')#, n='%sVizShape_'%curChar)
        
        pm.setAttr('%s.filterPolys'%gtoViz, 1)
        pm.setAttr('%s.filterCurves'%gtoViz, 0)
        pm.setAttr('%s.filterNURBS'%gtoViz, 0)
        pm.setAttr('%s.filterPoints'%gtoViz, 0)
        pm.setAttr('%s.filterPattern'%gtoViz, '*body_ShapeN*')        
        
        pm.setAttr('%s.cacheStartFrame'%gtoViz, startFrame)
        pm.setAttr('%s.cacheEndFrame'%gtoViz, endFrame)
        pm.expression(s='%s.currentTime = frame'%gtoViz)
        
        pm.setAttr('%s.animFile'%gtoViz, cacheFilename)
        if ggcp.hasReference:
            pm.setAttr('%s.refFile'%gtoViz, ggcp.referenceFilename)
        else:
            pm.warning('No reference gto found. GtoViz will be slower.')
            pm.setAttr('%s.refFile'%gtoViz, cacheFilename)
        
        gtoViz.addAttr('originalName', dt="string")
        gtoViz.addAttr('podFile', dt="string")
        gtoViz.addAttr('originalSeq', dt="string")
        gtoViz.addAttr('originalChar', dt="string")
        pm.setAttr('%s.podFile'%gtoViz, podPath, type="string")
        curSeq=str(self.animLibComboBox.currentText())
        curChar=str(self.characterComboBox.currentText())
        pm.setAttr('%s.originalSeq'%gtoViz, curSeq)
        pm.setAttr('%s.originalChar'%gtoViz, curChar)
        gtoTrans = gtoViz.listRelatives(p=True)[0]
        pm.setAttr('%s.scaleX'%gtoTrans, l=True)
        pm.setAttr('%s.scaleY'%gtoTrans, l=True)
        pm.setAttr('%s.scaleZ'%gtoTrans, l=True)
        pm.setAttr('%s.rotateOrder'%gtoTrans, l=True)
        
        origName = NAMES_INFO[bdNamingConventions.getCharacterFromPod(podPath)]['fullname']
        pm.setAttr('%s.originalName'%gtoViz, origName, type="string")
        pm.setAttr('%s.label'%gtoViz, origName, type="string")
        
        vizName = curChar + '_' + curSeq + '_Viz_'
        gtoTrans.rename(vizName)
        
        updateWindow()
 
    #### Offset the animation in time       
    def offsetTime(self, value):
        selObj = pm.ls(sl=True, dag=True, s=True)
        for obj in selObj:
            if obj.type() == 'TipGtoView':
                pm.setAttr('%s.timeOffset'%obj, value)

    #### Error dialog if more than one GtoViz is selected                   
    def singleVizErrorMessage(self):      
        errMess = 'Select a single TipGtoViz for publish'
        error = QMessageBox(QMessageBox.Warning, "Warning", errMess, QMessageBox.Cancel, self)
        error.exec_()
    
    
    def updateVersion(self, viz):
        seq = pm.getAttr('%s.originalSeq' % viz)
        char = pm.getAttr('%s.originalChar' % viz)
        podFile = pm.getAttr('%s.podFile' % viz)
        dbPod = getInfoFromFile(podFile)
        latestVersion = getLatestVersion(dbPod.production, dbPod.edition, dbPod.type, dbPod.name)
        latestPodPath = getAssetPath(dbPod.production, dbPod.edition, dbPod.type, dbPod.name, version=latestVersion)
        if latestVersion == dbPod.version:
            print '%s %s is up to date: nothing to update.' % (seq, char)
            return
        msg = '%s %s is out of date.\nUpdate to latest version (r%s)?' % (seq, char, latestVersion)
        ret = QMessageBox.question(self, "Update AnimLib", msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if not ret == QMessageBox.Ok:
            return
        ggcp = GtoGeometryCachePod.fromPodFile(latestPodPath)
        pm.setAttr('%s.animFile'%viz, ggcp.cacheFilename)
        pm.setAttr('%s.podFile'%viz, latestPodPath, type="string")
        if ggcp.hasReference:
            pm.setAttr('%s.refFile'%viz, ggcp.referenceFilename)
        else:
            pm.warning('No reference gto found. GtoViz will be slower.')
            pm.setAttr('%s.refFile'%viz, cacheFilename)
    
    
    @staticmethod
    def writeRetimeFile(viz, pubShot):
        '''
        Write the animated data on the currentTime attribute to a txt file.
        '''
        tmpPath = None
        # Return None if the attribute is not keyed.
        
        if pm.keyframe('%s.currentTime'%viz, query=True, keyframeCount=True):
            # get framelist from pod
            podFile = str(pm.getAttr('%s.podFile'%viz))
            ggcp = GtoGeometryCachePod.fromPodFile(podFile)
            ggcp.startFrame = pm.playbackOptions(q=True, animationStartTime=True)
            ggcp.endFrame = pm.playbackOptions(q=True, animationEndTime=True)
            frameList = ggcp.frameNumberList()
#             offset = float(pm.getAttr('%s.timeOffset'%viz))
#             frameList = [frame + offset for frame in ggcp.frameNumberList()]
            
            # Get curve data
            animCurveData = list()
            for frame in frameList:
                value = pm.keyframe(viz, query=True, time=[frame], attribute='currentTime', eval=True)
                assert len(value) == 1, '%s keyframes found for time %s. One expected.' % (len(value), frame)
                animCurveData.append([frame, value[0]])

            # Write it out to a temp file
            selCharName = str(pm.getAttr('%s.label'%viz))
            if not tmpPath:
                name = '_'.join(['animLib', 'bd', pubShot, selCharName, 'retime.txt'])
                tmpPath = os.path.join(tempfile.gettempdir(), name)
            fh = open(tmpPath, 'w')
            for time, value in animCurveData:
                fh.write('%s %s\n' % (time, value))
            fh.close()
            
        return tmpPath
            
##### Begin GUI interaction #####

    @pyqtSignature("int")
    def on_animOffsetHSlider_valueChanged(self):
        value = self.animOffsetHSlider.value()
        self.animOffsetSpinBox.setValue(value)
        self.offsetTime(value)
        
    @pyqtSignature("int")
    def on_animOffsetSpinBox_valueChanged(self):
        value = self.animOffsetSpinBox.value()
        self.animOffsetHSlider.setValue(value)
        self.offsetTime(value)

    @pyqtSignature("int")
    def on_animLibComboBox_currentIndexChanged(self):
        self.addLibChars()
        
    @pyqtSignature("int")
    def on_publishAsComboBox_currentIndexChanged(self):
        curChar = self.publishAsComboBox.currentText()
        selObj = self.selVizNode   
        if not selObj:
            return    
        pm.setAttr('%s.label'%selObj, '%s'%curChar, type="string")
        
        # Set the color of the GtoViz to match the normal animated character color
        character = bdNamingConventions.getCharacterFromFullname(curChar)
        try:
            color = NAMES_INFO[character]['color']
            pm.setAttr('%s.color'%selObj, color, type="double3")
        except:
            pass


    @pyqtSignature("int")
    def on_seqComboBox_currentIndexChanged(self):
        self.shotComboBox.clear()
        curSeq = self.seqComboBox.currentText()
        shots = Shot.selectBy(production='bd', sequence='%s'%curSeq)
        for s in shots:
            self.shotComboBox.addItem(s.name)

    @pyqtSignature("")
    def on_importAnimPushButton_clicked(self):
        try:
            podPath = self.getPodPath()
            self.createGtoViz(podPath)
        except Exception, msg:
            errMess = '%s animation for %s does not exist\nError: %s'%(self.characterComboBox.currentText(), self.animLibComboBox.currentText(), msg)
            error = QMessageBox(QMessageBox.Warning, "Warning", errMess, QMessageBox.Cancel, self)
            error.exec_()
            

    #### Do the actual publishing
    @pyqtSignature("")
    def on_publishPodPushButton_clicked(self):
        selChars = pm.ls(sl=True, dag=True, s=True)
        if len(selChars) != 1:
            self.singleVizErrorMessage()
        else:            
            selChar = selChars[0]
            if selChar.type() != "TipGtoView":
                self.singleVizErrorMessage()
            else:
                selCharName = str(pm.getAttr('%s.label'%selChar))
                gtoTrans = selChar.listRelatives(p=True)[0]
                selCharMatrix = pm.datatypes.MatrixN(pm.xform(gtoTrans, query=True, absolute=True, worldSpace=True, matrix=True))
                selCharMatrix.shape = (16,1)
                selCharMatrix = [float(i[0]) for i in selCharMatrix]
                pubSeq = str(self.seqComboBox.currentText())
                pubShot = str(self.shotComboBox.currentText())
                animOffset = int(pm.getAttr('%s.timeOffset'%selChar))
#                 animIncr = pm.getAttr('%s.cacheFrameIncrement'%selChar)
#                 animStart = pm.getAttr('%s.cacheStartFrame'%selChar)
#                 animEnd = pm.getAttr('%s.cacheEndFrame'%selChar)
#                 cacheFile = pm.getAttr('%s.cacheFile'%selChar)
                podFile = str(pm.getAttr('%s.podFile'%selChar))
                origName = str(pm.getAttr('%s.originalName'%selChar))
                origChar = str(pm.getAttr('%s.originalChar'%selChar))
                origShot = str(pm.getAttr('%s.originalSeq'%selChar))
                
                text = ['Kick off publish with the following values?']
                text.append('')
                text.append('Selected:   ' + origChar)
                text.append('From Shot:  ' + origShot)
                text.append('')
                text.append('Publish As: ' + selCharName)
                text.append('Publish To: ' + pubShot)
                text.append('')
                text.append('Notes:')

                defaultNotes = origChar + ' from ' + origShot                
                notes, ok = QInputDialog.getText(self, 'Anim Lib Publish', '\n'.join(text), QLineEdit.Normal, defaultNotes)
           
                if ok:
                    if not notes:
                        QMessageBox.warning(self, 'Invalid Publish Notes', 'Cannot publish without notes.  Publish aborted.' + 
                                                                            '\nPlease publish again with notes.')
                        return
                        
                    print 'Publishing to shot: ', pubShot
                    print 'podPath', podFile
                    print 'transform', selCharMatrix
                    print 'offset', animOffset
                    print 'publishAsWolf', selCharName
                    print 'publishFromName', origName
                    print 'notes', notes
                    retimePath = self.writeRetimeFile(selChar, pubShot)
                    if retimePath:
                        print 'Wrote retime file to: %s' % retimePath
                    animLibFarmJob.publish(pubShot, 
                                            podFile, 
                                            selCharMatrix, 
                                            animOffset, 
                                            selCharName, 
                                            origName, 
                                            str(notes), 
                                            retimeCurve=retimePath)

##### Begin GUI interaction #####

#### Show the animation lib window          
def showAnimLibWindow():
    global animLibWindow
    animLibWindow = AnimLibWindow()
    animLibWindow.show()
    vizNodes = pm.ls(type='TipGtoView')
    for viz in vizNodes:
        animLibWindow.updateVersion(viz)
    updateWindow()

#### Callbacks for scene interaction, to maintain parity between the interface and the selected GtoViz 
def updateWindow():
    selObj = pm.ls(sl=True, dag=True, s=True)
    
    vizNodes = [node for node in selObj if node.type() == 'TipGtoView']
    
    animLibWindow.selVizNode = None
    
    animLibWindow.animOffsetHSlider.setEnabled(False)
    animLibWindow.animOffsetSpinBox.setEnabled(False)
    animLibWindow.publishAsComboBox.setEnabled(False)  
    animLibWindow.seqComboBox.setEnabled(False)
    animLibWindow.shotComboBox.setEnabled(False)
    animLibWindow.publishPodPushButton.setEnabled(False)
    
    if not vizNodes:
        return

    animLibWindow.animOffsetHSlider.setEnabled(True)
    animLibWindow.animOffsetSpinBox.setEnabled(True)        

    offsetVal = pm.getAttr('%s.timeOffset'%vizNodes[-1])
    animLibWindow.animOffsetHSlider.setValue(offsetVal)
        
    if len(vizNodes) == 1:
        obj = vizNodes[0]
        animLibWindow.selVizNode = obj
        
        animLibWindow.publishAsComboBox.setEnabled(True)  
        animLibWindow.seqComboBox.setEnabled(True)
        animLibWindow.shotComboBox.setEnabled(True)
        animLibWindow.publishPodPushButton.setEnabled(True)
        
        animLibWindow.populateOutputs()

        seqVal = pm.getAttr('%s.originalSeq'%obj)
        charVal = pm.getAttr('%s.originalChar'%obj)
        animLibWindow.animLibComboBox.setCurrentIndex(animLibWindow.animLibComboBox.findText(seqVal))
        animLibWindow.characterComboBox.setCurrentIndex(animLibWindow.characterComboBox.findText(charVal))
        wolfVal = pm.getAttr('%s.label'%obj)
        origVal = pm.getAttr('%s.originalName'%obj)                
        animLibWindow.publishAsComboBox.setCurrentIndex(animLibWindow.publishAsComboBox.findText(wolfVal))
