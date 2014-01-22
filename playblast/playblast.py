#!/usr/bin/env mayapy
#*******************************************************************************
# Copyright (c) 2012 Tippett Studio. All rights reserved.
# $Id$ 
#*******************************************************************************

import sys
import os
import logging
import inspect
import subprocess

try:
    from maya import cmds
    from maya import mel
except ImportError:
    from tip.maya.commandPort import CommandPort
    cmds = CommandPort("cmds")
    mel = CommandPort("mel")

from tip.utils.path import isNetworkPath
from tip.utils.framespec import FrameSpec
import tip.batcho

IMAGE_FORMAT_DICT = {
                    'als': 6,
                    'cin': 11,
                    'dds': 35,
                    'eps': 9,
                    'gif': 0,
                    'jpeg': 8,
                    'iff': 7,
                    'psd': 31,
                    'png': 32,
                    'yuv': 12,
                    'rla': 2,
                    'sgi': 5,
                    'pic': 1,
                    'tga': 19,
                    'tif': 3,
                    'bmp': 20,
                    'tim': 63
                    }
                    

class ImageFormatException(Exception):
    pass
    

class FilenameException(Exception):
    pass

   
def getPanel():
    isModelPanel = False
    panel = cmds.getPanel(withFocus=True)
    panelType = cmds.getPanel(typeOf=panel)
    if panelType == "modelPanel":   
        isModelPanel = True
    return isModelPanel, panel 


def scenePath():
    return cmds.file(q=True, expandName=True)


def sceneModified():
    return cmds.file(q=True, modified=True)


def getTimeSlider():
    return cmds.playbackOptions(q=True, minTime=True), cmds.playbackOptions(q=True, maxTime=True)


def getSoundInfo():
    gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')  # seriously maya?
    sound = cmds.timeControl(gPlayBackSlider, q=True, sound=True)
    if sound:
        soundfile = cmds.sound(sound, q=True, file=True)
        soundOffset = cmds.getAttr('%s.offset' % sound)
        return str(soundfile), soundOffset
    else:
        return None, None


def launchViewer(blastFilename, format, start, end, viewer, viewerArgs):
    '''
    Assemble the command to view the playblast, and run it.  Supports rv, flipper, and fcheck.
    '''
    viewCmd = list()  
    soundfile, soundOffset = getSoundInfo()  
    if viewer == "rv":
        viewCmd = ['rv']
        filesToView = blastFilename + '.' + ('%04d-%04d#' % (start, end)) + '.' + format
        viewCmd.extend(str(viewerArgs).split())
        viewCmd.extend(['-play'])
        viewCmd.extend(['-c'])
        if soundfile:
            rvOffset = str(-(start / 59.94))
            viewCmd.extend(['[', filesToView, soundfile, '-ao', rvOffset, ']'])
        else:
            viewCmd.extend([filesToView])
    elif viewer == "flipper":
        viewCmd = ['flipper']
        viewCmd.extend(str(viewerArgs).split())
        filesToView = blastFilename + '.' + ('%04d-%04d' % (start, end)) + '.' + format
        viewCmd.extend([str(filesToView)])
        if soundfile:
            viewCmd.extend(['-sound', soundfile, '-slip', str(soundOffset)])
    elif viewer == "fcheck":
        viewCmd = ['fcheck']
        viewCmd.extend(str(viewerArgs).split())
        viewCmd.extend(["-n", str(start), str(end), str(1)])
        filesToView = blastFilename + '.' + '#' + '.' + format
        viewCmd.extend([filesToView])        
    print '>>> ' + ' '.join(viewCmd)
    subprocess.Popen(viewCmd)  


def playblastLocal(blastFilename, format, start, end, offscreen, width, height):
    '''
    Perform a playblast.
    '''
    # Check
    if format not in IMAGE_FORMAT_DICT:
        raise ImageFormatException, 'Invalid image format: %s' % format

    # Set the image format from the list and backup the old one
    oldRenderFormat = cmds.getAttr('defaultRenderGlobals.imageFormat')
    cmds.setAttr('defaultRenderGlobals.imageFormat', IMAGE_FORMAT_DICT[format])

    # Do the blast
    cmds.playblast(filename=blastFilename,
                   format='image',
                   startTime=start,
                   endTime=end,
                   forceOverwrite=True,
                   viewer=False,
                   offScreen=offscreen,
                   widthHeight=[int(width), int(height)],
                   percent=100
                   )
    
    # Restore the old render globals image format
    cmds.setAttr('defaultRenderGlobals.imageFormat', oldRenderFormat) 
    

def playblastFarmJob(mayaScene, playblastFilename, **kwargs):
    '''
    Create a playblast job to send to the farm, and return the job.
    '''

    # Check if args in extras are valid
    validArgs = set(inspect.getargspec(playblastOnFarm)[0]) - set(inspect.getargspec(playblastFarmJob)[0])
    for arg in kwargs:
        assert arg in validArgs, 'Invalid argument: %s.' % arg

    # Check path
    if not os.path.exists(mayaScene):
        raise FilenameException('Scene %s does not exist.' % mayaScene)
    if not isNetworkPath(mayaScene):
        raise FilenameException('Scene %s is not network visible.' % mayaScene)
    blastDir = os.path.dirname(playblastFilename) 
    if not os.path.exists(blastDir):
        raise FilenameException('Directory %s does not exist.' % blastDir)        
    if not isNetworkPath(blastDir):
        raise FilenameException('Directory %s is not network visible.' % blastDir)

    # Framerange
    framespec = None
    if 'start' in kwargs and 'end' in kwargs:
        framespec = FrameSpec('%s-%s:1' % (kwargs['start'], kwargs['end']))
        kwargs['start'] = '%FS%'
        kwargs['end'] = '%FE%'

    farmCmd = 'playblastOnFarm -scene %s -fo %s ' % (mayaScene, playblastFilename)
    farmCmd += ' '.join(['-%s %s' % (key, value) for key,value in kwargs.items()])
    
    # Create the job
    jobName = 'playblast_%s' % os.path.basename(mayaScene)
    tags = ['playblast']
    farmJob = tip.batcho.job.Job(tip.batcho.utils.makeBatchoName(jobName), tags=tags)

    # Create the script
    scriptName = 'playblastScene'
    requirements = ["noprman","linux","maya"]
    if framespec: # Batch the tasks
        batchIncrement = 10
        if len(framespec) > 100:
            batchIncrement = int(len(framespec)/batchIncrement)
        script = tip.batcho.script.BatchFsFeScript(farmJob,
                                      tip.batcho.utils.makeBatchoName(scriptName),
                                      frames=framespec,
                                      batch=batchIncrement,
                                      requires=requirements,
                                      cmdline=farmCmd)        
    else: # else just do the whole range in one task
        script = tip.batcho.script.RunOnceScript(farmJob,
                                      tip.batcho.utils.makeBatchoName(scriptName),
                                      requires=requirements,
                                      cmdline=farmCmd)
    return farmJob


def playblastOnFarm(mayaScene, fileout='/tmp/playblast.tif', format='tif', width=640, height=480, start=None, end=None, panel=None):
    '''
    The method that gets called from a farm machine to perform a playblast.
    '''
    # Set up logging
    logLevel = logging.DEBUG
    logFormat = "[playblastOnFarm] %(asctime)-15s %(levelname)s -- %(message)s"
    logging.basicConfig(level=logLevel, format=logFormat)

    try:
        # Pipe script editor output to log
        cmds.scriptEditorInfo(wh=True, hfn='/dev/stderr')
        
        # Read Scene
        logging.info('Maya is opening file: ' + mayaScene)
        cmds.file(mayaScene, open=True, force=True)
        logging.info('File opened succesfully.')
        
        # Might be unecessary, but ensure the desired UI panel for playblasting
        if panel:
            cmds.setFocus(panel)
#         else:
#             # Create a new window in case for whatever reason there isn't one
#             window = cmds.window(title='playblastWindow')
#             layout = cmds.paneLayout()
#             panel = cmds.modelPanel()
#             editor = cmds.modelPanel(panel, q=True, modelEditor=True)
#             cmds.showWindow(window)
#             cmds.setFocus(window)

        # Check/set framerange
        if not start:
            start = cmds.playbackOptions(q=True, minTime=True)
        else:
            cmds.playbackOptions(e=True, minTime=float(start)) 
        if not end:
            end = cmds.playbackOptions(q=True, maxTime=True)
        else:
            cmds.playbackOptions(e=True, maxTime=float(end))

        logging.info('Frame range is %s-%s.' % (start, end))
        assert start < end, "End frame is not greater than start frame."

        # Set renderglobal imageformat
        cmds.setAttr('defaultRenderGlobals.imageFormat', IMAGE_FORMAT_DICT[format])
        logging.info('Image format: %s' % format)

        playblastArgs = {
                        'filename': fileout,
                        'startTime': start,
                        'endTime': end,
                        'format': 'image',
                        'widthHeight': [int(width), int(height)],
                        'percent': 100,
                        'viewer': False,
                        'offScreen': True,
                        'forceOverwrite': True
                        }
                        #'sequenceTime' = True
                        #'framePadding' = 4 (default)
                        #'rawFrameNumbers' = True (maybe)
        logging.info('Playblasting with arguments: %s' % playblastArgs)
        logging.debug('Playblasting with arguments: %s' % playblastArgs)
        cmds.playblast(**playblastArgs)
        logging.info('Playblast completed succesfully.')
        
    except Exception, e:
        logging.error(e)

    finally:
        # Exit
        cmds.quit(abort=True)
