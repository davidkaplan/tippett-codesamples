#
#*******************************************************************************
# Copyright (c) 2007 Tippett Studio. All rights reserved.
# $Id$
#*******************************************************************************
#
# This is a plugin script to be used by the Tippett tool podPublish.
# It validates the data in the node, copies files to where they belong,
# and sets the pod's data to the new locations.
#
# string PUBLISH_TYPE : what this pod node type will be published as in the tip db.
# function pluginMain(node, destinationPath) : pod node & where it will be going.
# function pluginValidate(node) : pod node
#

import os
import pod
import logging
from tip.studio.publish import pm
from tip.utils.framespec import replaceFrameSymbols

PUBLISH_TYPE = "fxRib"
VALID_CHILD_NODE_TYPES = ['MuInstancer', 'RiGto']

# The input pod node (and its children) had best have these parameters
requiredFxRibsParameters = ['ribs', 'nodes', 'startFrame', 'endFrame', 'frameIncrement']
requiredMuInstancerParameters = ['ribIdentifier', 'cacheFiles', 'muScript',
                                        'startFrame', 'endFrame', 'frameIncrement']
requiredRiGtoParameters = ['ribIdentifier', 'cacheFiles',
                                        'startFrame', 'endFrame', 'frameIncrement']

#############################################
def podNodeCopy(node):
    """
    There is no way to copy a POD object, so we write it to a string,
    re-parse it, find the node, and return THAT.
    Named and typed nodes only.
    """
    assert node.name() and node.type()
    asStr = """%s %s = {\n%s\n};""" % (node.type()[0], node.name(), node.write())
    podCopy = pod.Pod(asStr, "copy")
    # Re-wrap in pod.Node() to avoid a segfault when podCopy goes out of scope.
    return pod.Node(podCopy[node.name()].asNode())


#############################################
def pmMakeDir(path):
    assert "$" not in path, "Unresolved variable in '%s'" % path
    if not os.path.exists(path):
        orig_umask = os.umask(022)
        logging.debug("Making directory %s" % path)
        pm.makedirs(path)
        pm.chmod(path, 0755)
        os.umask(orig_umask)


#############################################
def validateAllFxRibsFiles(node, frameNumList):
    ribFilename = node['ribs'].asString()
    for frameNum in frameNumList:
        srcFile = replaceFrameSymbols(ribFilename, frameNum)
        if not os.path.exists(srcFile):
            return False
    return True
      
  
#############################################
def validateAllCacheFiles(node, frameNumList):
    cacheFilename = node['cacheFiles'].asString()
    for frameNum in frameNumList:
        srcFile = replaceFrameSymbols(cacheFilename, frameNum)
        if not os.path.exists(srcFile):
            return False
    return True
  
      
#############################################
def validateAllMuInstancerFiles(node, frameNumList):
    if not validateAllCacheFiles(node, frameNumList):
        return False
          
    muFilename = node['muScript'].asString()
    for frameNum in frameNumList:
        srcFile = replaceFrameSymbols(muFilename, frameNum)
        if not os.path.exists(srcFile):
            return False
    return True

   
#############################################
def validateAllRiGtoFiles(node, frameNumList):
    return validateAllCacheFiles(node, frameNumList)


#############################################
def frameNumListFromNode(node):
    """
    Given a pod node, return a list of floats representing all frame numbers.
    """
    # Build the list of frames
    frameNumList = list()
    startFrame = node['startFrame'].asFloat()
    endFrame = node['endFrame'].asFloat()
    frameInc = node['frameIncrement'].asFloat()
    sf = startFrame
    while sf <= endFrame:
        frameNumList.append(sf)
        sf += frameInc
    return frameNumList


#############################################
def scanToRibAttribute(ribAttribute, filePointer):
    """
    Given a file pointer (presumably reset to the start of the file), move it
    to the beginning of the line immediately following the attribute declaration.
    Returns True if successful, false if the attribute does not exist in the rib.
    """
    for line in filePointer:
        strippedLine = line.strip()
        if not strippedLine.startswith("Attribute"):
            continue
        # Since we don't have a real rib parser, parse the rib...
        if strippedLine == "AttributeBegin" or strippedLine == "AttributeEnd":
            continue

        quotedElements = [x.strip() for x in strippedLine.split('"')]
        if not quotedElements[1] == 'identifier' or not quotedElements[3] == 'name':
            continue

        try:
            startBracketIndex = quotedElements.index('[')
        except:
            continue
        elementName = quotedElements[startBracketIndex+1]
        if elementName == ribAttribute:
            return True

    return False

#############################################
def pluginValidate(node):
    """
    This function validates a given pod node, insuring parameters and files exist.
    """
    # Validate the type
    logging.info("Validating FxRib node %s" % node.name())
    assert isinstance(node, pod.Node)
   
    # Insure all necessary parameters exist for top node
    assert all([rp in node.valueNames() for rp in requiredFxRibsParameters])

    # Insure all the files exist for the top node
    frameNumList = frameNumListFromNode(node)
    if not validateAllFxRibsFiles(node, frameNumList):
        raise RuntimeError("Not all files specified in FuratorNode %s are present" % node.name())

    # Drill into its children and insure...
    for child in node['nodes'].asNode().unnamedValues():
        try:
            childNode = child.asNode()
        except:
            raise RuntimeError("Child %s is missing from FxRib node %s." % (child.asNodeLink()[0], node.name()))

        # ...their parameters exist.
        if childNode.type()[0] == 'MuInstancer':
            assert all([rp in childNode.valueNames() for rp in requiredMuInstancerParameters])
            # ...the particle and script files exist
            childFrameNumList = frameNumListFromNode(childNode)
            if not validateAllMuInstancerFiles(childNode, childFrameNumList):
                raise RuntimeError("Not all files specified in MuInstancer %s are present" % childNode.name())
        elif childNode.type()[0] == 'RiGto':
            assert all([rp in childNode.valueNames() for rp in requiredRiGtoParameters])
            # ...the particle and script files exist
            childFrameNumList = frameNumListFromNode(childNode)
            if not validateAllRiGtoFiles(childNode, childFrameNumList):
                raise RuntimeError("Not all files specified in RiGto %s are present" % childNode.name())
        else:
            raise RuntimeError("Child %s has invalid nodeType %s" % (childNode.name(), childNode.type()))

        # ...each rib contains all the required parameters
        ribIdentifier = childNode.value('ribIdentifier').asString()
        ribFilename = node.value('ribs').asString()
        for frameNum in childFrameNumList:
            srcFile = replaceFrameSymbols(ribFilename, frameNum)
            fp = open(srcFile)
            if not scanToRibAttribute(ribIdentifier, fp):
                raise RuntimeError("Attribute %s is missing from rib %s." % (ribIdentifier, srcFile))
            fp.close()

##############################################
#   Several Methods for Copying Ribs
#
#   As above: In absence of a real rib parser, here we go...
#

def rib_Copy(srcFile, dstFile, node, publishPath):
    '''
    Given two open file handles, copies a rib file line by line from srcFile
    to dstFile.  Looks for child nodes of the parent node and replaces paths
    in the DSO lines where applicable.
    '''
    for line in srcFile:
        if line.startswith("AttributeBegin"): 
            dstFile.write(line) 
            rib_findIdentifier(srcFile, dstFile, node, publishPath)
        else:
            dstFile.write(line)
       
def rib_findIdentifier(srcFile, dstFile, node, publishPath):
    '''
    Inside an attribute block, look for the expected attribute identifier call.
    '''
    # Set up a dictionary of child Shape names for easy lookup
    childIdentifier = ''; 
    childNameDict = dict()
    for child in node['nodes'].asNode().unnamedValues():
        childNode = child.asNode()
        key = childNode['ribIdentifier'].asString()
        assert key not in childNameDict, 'NON-UNIQUE RIB IDENTIFIER: "%s" found on node "%s" is already associated with node "%s".' \
                                                                                % (key, childNode.name(), childNameDict[key].name())
        childNameDict[key] = childNode

    # Continue looping through file
    for line in srcFile:
        lineElements = [x.strip('"') for x in line.split(' ')]
      
        # If AttributeEnd, start over
        if line.startswith("AttributeEnd"):
            dstFile.write(line)
            rib_Copy(srcFile, dstFile, node, publishPath)
            return
        # looking for line: Attribute "identifier" "name" ["childName"]
        elif line.startswith("Attribute"):   
            try:
                if lineElements[1] == 'identifier' and lineElements[2] ==  'name':
                    elementName = lineElements[3].strip('[]"\n')
                    if elementName in childNameDict.keys():
                        childIdentifier = elementName;
            except:
                pass
        # If child already found for AttributeBegin block, look for the procedural call
        elif line.startswith("Procedural") and childIdentifier:
            line = rib_modifyDSO(srcFile, line, childNameDict[childIdentifier], publishPath)
        dstFile.write(line)     
      
def rib_modifyDSO(srcFile, line, childNode, publishPath):
    '''
    Modify a procedural call in the rib to replace the working paths with
    our new publish paths to the gto's, and optionally to the .mu if the
    child is of type MuInstancer.  Returns the modified or unmodified line.
    '''
    lineElements = [x.strip('[]"\n') for x in line.split(' ')]
    # dsoPath = lineElements[2]
    if lineElements[1] == "DynamicLoad":
        workingPath = os.path.dirname(srcFile.name)
        pubSubPath = os.path.join(publishPath, childNode.name())
        line = line.replace(workingPath, pubSubPath)
    return line

#############################################

#####################
#                   #
#       MAIN        #
#                   #
#####################

def pluginMain(node, publishPath):
    """
    This function is intended to move data in a pod node to a given path.
    It makes a deep copy of the pod node and returns a list of all nodes
    it needed to touch to publish.
    """
    # The list of nodes to be returned
    returnNodeList = list()
  
    # Copy the pod node to a new one that we can modify
    newNode = podNodeCopy(node)
    returnNodeList.append(newNode)
  
    # Get frame range
    frameNumList = frameNumListFromNode(newNode)
    ribFileName = newNode['ribs'].asString()
  
    # Make dir for new ribs
    ribPath = os.path.join(publishPath, 'ribs')
    pmMakeDir(ribPath)
  
    # Copy Ribs
    for frameNum in frameNumList:
        # Set up paths
        srcPath = replaceFrameSymbols(ribFileName, frameNum)
        dstPath = os.path.join(ribPath, os.path.basename(srcPath))   
        logging.info("Copying %s -> %s" % (srcPath, dstPath))
      
        # Create new file as pm for consistent permissions
        pm.createEmptyFile(dstPath)
        dstFile = open(dstPath, 'w')
        srcFile = open(srcPath, 'r')
      
        # Copy and modify DSO paths at the same time
        logging.info("Copying %s -> %s" % (srcPath, dstPath))
        rib_Copy(srcFile, dstFile, node, publishPath)
      
        # Close files
        srcFile.close()
        dstFile.close()
      
        # Lock it down
        pm.chmod(dstPath, 0444)
  
    # Lock down the rib dir
    pm.chmod(ribPath, 0755)
      
    ## TO DO: check that ribs exist 

    # Change rib path in node
    finalRibFilename = os.path.join(ribPath, os.path.basename(ribFileName))
    newNode.setValue('ribs', pod.Value(finalRibFilename))
    logging.info("Modifying project point to new ribs: %s" % finalRibFilename)
  
    # TO DO: Check for Duplicate Children

    # Loop through children
    for child in node['nodes'].asNode().unnamedValues():
        # Get child node, add to list
        childNode = child.asNode()
        returnNodeList.append(childNode)
        logging.info("Adding child node %s to project" % childNode.name())
      
        # Set up paths
        gtoPath = os.path.join(publishPath, childNode.name())
        pmMakeDir(gtoPath)
  
        # Get frame range.  Children can have different frame range than parent.
        childFrameNumList = frameNumListFromNode(childNode)
        gtoFileName = childNode['cacheFiles'].asString()

        # Copy gto's
        for frameNum in childFrameNumList:
            srcFile = replaceFrameSymbols(gtoFileName, frameNum)
            dstFile = os.path.join(gtoPath, os.path.basename(srcFile))
            logging.info("Copying %s -> %s" % (srcFile, dstFile))
            pm.copy(srcFile, dstFile)
            pm.chmod(dstFile, 0444)
       
        # TO DO: check that cacheFiles exist

        # Write new gto path in node
        finalGtoFilename = os.path.join(gtoPath, os.path.basename(gtoFileName))
        childNode.setValue('cacheFiles', pod.Value(finalGtoFilename))

        # Copy mu script if node is type MuInstancer
        if childNode.type() == ['MuInstancer']:
            # Get path
            scriptFile = childNode['muScript'].asString()
            finalScriptFile = os.path.join(gtoPath, os.path.basename(scriptFile))
            logging.info("Copying %s -> %s" % (scriptFile, finalScriptFile))
            # Copy
            pm.copy(scriptFile, finalScriptFile)
            pm.chmod(finalScriptFile, 0444)               
      
            # Write new mu path in node
            childNode.setValue('muScript', pod.Value(finalScriptFile))
      
        # Lock down gto dir
        pm.chmod(gtoPath, 0755)

    # Return the list of modified nodes
    logging.info("Exiting FxRib plugin.")
    return returnNodeList

if __name__ == '__main__':

    podPath = '/work/projects/muInstPodPublish/snow_particles_body_publish.pod'
    publishPath = '/work/projects/muInstPodPublish/pub/'
  
    inPod = pod.Pod(podPath)
    objNode = inPod.namedValues()[0].asNode()

    print objNode.name()
    print objNode.type()[0]

    pluginMain(objNode, publishPath)
