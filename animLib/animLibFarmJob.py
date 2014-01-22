#!/usr/bin/env python
#*******************************************************************************
# Copyright (c) 2012 Tippett Studio. All rights reserved.
# $Id$ 
#*******************************************************************************

import sys, os
import pod
import subprocess
import logging
import shutil

from tip.utils.cmdline import Parser, UsageError
from tip.utils.path import isNetworkPath
from tip.gtoCache.podCache import GtoGeometryCachePod
from tip.gtoCache.podFarmJob import TEMP_POD_SPOOL_DIR

from tip.batcho.utils import *
from tip.batcho.job import *
from tip.batcho.script import *
from tip.batcho.task import *

from tip.db.studio import Shot

SHOW = os.getenv('TS_SHOW')
USER = os.getenv('USER', 'nobody')
assert SHOW == 'bd', 'SHOW ENVIRONMENT MUST BE BREAKING DAWN ("bd")'


def checkInput(shot, podPath, transform, offset, publishAsWolf, publishFromName):
    '''
    Check arguments for proper values and formatting
    '''
    assert shot in [showShot.name for showShot in Shot.selectBy(production=SHOW)], 'Invalid shot: %s' % shot
    assert os.path.exists(podPath), 'Invalid path to pod file'
    assert os.path.splitext(podPath)[1] == '.pod', 'Given pod file has invalid extension'
    assert isNetworkPath(podPath), 'Pod path is not network accessible! %s' % podPath
    assert len(transform) == 16, 'Transform matrix has dimensions: %s.  Expected a 16x1 list.' % len(transform)
    assert type(offset) in [int, float], 'Offset %s is not a number' % type(offset)
    assert publishAsWolf and publishFromName, 'Creature names not defined'
    
    ggcp = GtoGeometryCachePod.fromPodFile(podPath)
    assert ggcp.exists(), 'Cache directory %s does not exists.' % ggcp.cacheDir
    assert ggcp.isComplete(), 'Cache is incomplete'
    
def publish(shot, podPath, transform, offset, publishAsWolf, publishFromName, notes, noFarm=False, noPublish=False, retimeCurve=None):
    '''
    Construct the command line argument, and send to batcho (or run locally)
    '''
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Format and check input (fail before we get to batcho)
    checkInput(shot, podPath, transform, offset, publishAsWolf, publishFromName)
    
    # Cast transform to string for argument
    xformArg = ' '.join([repr(i) for i in transform])
    
    # Construct commandline
    pubCmd = ['animLibPublish']
    pubCmd.extend(['-show', SHOW])
    pubCmd.extend(['-shot', shot])
    pubCmd.extend(['-pod', podPath])
    pubCmd.extend(['-offset', str(offset)])
    pubCmd.extend(['-publishAs', publishAsWolf])
    pubCmd.extend(['-publishFrom', publishFromName])
    pubCmd.extend(['-notes', notes])
    # If not publishing (keep files in temp dir
    if noPublish:
        pubCmd.append('-noPublish')           
    # Finally, put transform at the end because it is long
    pubCmd.extend(['-transform', xformArg])

    # To run locally:
    if noFarm:
        if retimeCurve:
            pubCmd.extend(['-retime', retimeCurve])
        try:
            logging.info('>>> %s' % ' '.join(pubCmd))
            subprocess.check_call(pubCmd)
        except subprocess.CalledProcessError, err:
            logging.exception(err)
            raise RuntimeError
        sys.exit(0)

    # Create batcho job
    jobName = '_'.join(['animLib', SHOW, shot, publishAsWolf])
    tags = ['animLib']
    job = Job(jobName, tags=tags) 
    
    # Create publish script
    pubScriptName = 'BD_publishCache'
    requirements = set(['noprman', 'linux'])
    pubScript = RunOnceScript(job, pubScriptName, cmdline=pubCmd, requires=requirements)

    # Move retime curve to network
    if retimeCurve:
        destTemp = os.path.join(TEMP_POD_SPOOL_DIR, os.path.basename(retimeCurve))
        shutil.copyfile(retimeCurve, destTemp)
        pubCmd.extend(['-retime', destTemp])  
            
    # Submit batcho job
    logging.info('>>> %s' % ' '.join(pubCmd))
    job.submit()



if __name__ == '__main__':
    
    podPath = '/show/bd/animlib/animlib1wolftugofwar/pub/geometryCache/vamp1/animlib1wolftugofwar.vamp1.r9.pod'

    show = 'bd'
    shot = 'test1animlib'  
    
    publishAsWolf = 'genVolturi2'
    publishFromName = 'genVolturi'
    
    offset = 0 
    transform = (1.0 , 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0, 0.0,
                 0.0, 0.0, 1.0, 0.0,
                 0.0, 0.0, 0.0, 1.0)

    notes = 'retime test'
    
    retime = '/tmp/animLib_bd_test1animlib_genVolturi_retime.txt'
    
    publish(shot, podPath, transform, offset, publishAsWolf, publishFromName, notes, noFarm=True, noPublish=True, retimeCurve=retime)
