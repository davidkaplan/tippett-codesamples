#!/usr/bin/env python
#*******************************************************************************
# Copyright (c) 2012 Tippett Studio. All rights reserved.
# $Id$ 
#*******************************************************************************

import os
import pod

from tip.gtoCache.podCache import GtoGeometryCachePod

assert os.getenv('TS_SHOW') == 'bd', 'SHOW ENVIRONMNET MUST BE SET TO "BD"'

WOLF_LIST = [
    'creature1bradywolf', 
    'creature1collinwolf', 
    'creature1embrywolf', 
    'creature1jacobwolf', 
    'creature1jaredwolf',
    'creature1leahwolf', 
    'creature1paulwolf', 
    'creature1quilwolf', 
    'creature1samwolf', 
    'creature1sethwolf',
    'creature1young1wolf', 
    'creature1young2wolf', 
    'creature1young3wolf', 
    'creature1young4wolf', 
    'creature1young5wolf',
    'creature1young6wolf',
    'creature1young7wolf'
    ]
  
  
VAMP_LIST = [
    'creature1genvolturi',
    'creature1genvolturi2',
    'creature1genvolturi3',
    'creature1genvolturi4',
    'creature1genvolturi5',
    'creature1genvolturi6',
    'creature1genvolturi7',
    'creature1genvolturi8',
    'creature1genvolturi9',
    'creature1genvolturi10',
    'creature1genvolturi11',
    'creature1genvolturi12',
    'creature1genvolturi13',
    'creature1genvolturi14',
    'creature1genvolturi15',
    ]
                         
    
CHARACTER_COLORS = {
    'creature1bradywolf':  (.243, .541, .1181), 
    'creature1collinwolf': (.227, .639, .620), 
    'creature1embrywolf':  (.9,   .876, .876), 
    'creature1jacobwolf':  (.5,   .152, .089), 
    'creature1jaredwolf':  (.344, .250, .181),
    'creature1leahwolf':   (.822, .497, .680), 
    'creature1paulwolf':   (.5,   .461, .447), 
    'creature1quilwolf':   (.394, .392, .554), 
    'creature1samwolf':    (.2,   .179, .179), 
    'creature1sethwolf':   (.634, .476, .250),
    'creature1young1wolf': (.451, .745, .820), 
    'creature1young2wolf': (.344, .250, .181), 
    'creature1young3wolf': (.5,   .461, .447), 
    'creature1young4wolf': (.5,   .461, .311), 
    'creature1young5wolf': (.725, .693, .569),
    'creature1young6wolf': (.316, .341, .341)
    }
    
CHARACTER_CODES = {
    'creature1bradywolf':   'BDW',
    'creature1collinwolf':  'CLW',
    'creature1embrywolf':   'EMW',
    'creature1jacobwolf':   'JCW',
    'creature1jaredwolf':   'JRW',
    'creature1leahwolf':    'LEW',
    'creature1paulwolf':    'PLW',
    'creature1quilwolf':    'QLW',
    'creature1samwolf':     'SMW',
    'creature1sethwolf':    'STW',
    'creature1young1wolf':  'Y1W',
    'creature1young2wolf':  'Y2W',
    'creature1young3wolf':  'Y3W',
    'creature1young4wolf':  'Y4W',
    'creature1young5wolf':  'Y5W',
    'creature1young6wolf':  'Y6W',
    'creature1young7wolf':  'Y7W',
    'creature1genvolturi':  'GAV',
    'creature1genvolturi2': 'GAV',
    'creature1genvolturi3': 'GAV',
    'creature1genvolturi4': 'GAV',
    'creature1genvolturi5': 'GAV',
    'creature1genvolturi6': 'GAV',
    'creature1genvolturi7': 'GAV',
    'creature1genvolturi8': 'GAV',
    'creature1genvolturi9': 'GAV',
    'creature1genvolturi10': 'GAV',
    'creature1genvolturi11': 'GAV',
    'creature1genvolturi12': 'GAV',
    'creature1genvolturi13': 'GAV',
    'creature1genvolturi14': 'GAV',
    'creature1genvolturi15': 'GAV',
    }       

CHARACTER_TOPNODES = {
    'creature1jacobwolf':   'bdJacobwolfBuiltTopNodeN_1',
    ###
    'creature1bradywolf':   'bdBradywolfBuiltTopNodeN_1',
    'creature1collinwolf':  'bdCollinwolfBuiltTopNodeN_1',
    'creature1embrywolf':   'bdEmbrywolfBuiltTopNodeN_1',
    'creature1jaredwolf':   'bdJaredwolfBuiltTopNodeN_1',
    'creature1leahwolf':    'bdLeahwolfBuiltTopNodeN_1',
    'creature1paulwolf':    'bdPaulwolfBuiltTopNodeN_1',
    'creature1quilwolf':    'bdQuilwolfBuiltTopNodeN_1',
    'creature1samwolf':     'bdSamwolfBuiltTopNodeN_1',
    'creature1sethwolf':    'bdSethwolfBuiltTopNodeN_1',
    'creature1young1wolf':  'bdYoung1wolfBuiltTopNodeN_1',
    'creature1young2wolf':  'bdYoung2wolfBuiltTopNodeN_1',
    'creature1young3wolf':  'bdYoung3wolfBuiltTopNodeN_1',
    'creature1young4wolf':  'bdYoung4wolfBuiltTopNodeN_1',
    'creature1young5wolf':  'bdYoung5wolfBuiltTopNodeN_1',
    'creature1young6wolf':  'bdYoung6wolfBuiltTopNodeN_1',
    'creature1young7wolf':  'bdYoung7wolfBuiltTopNodeN_1',
    ###
    'creature1genvolturi':  'bdGenvolturiBuiltTopNodeN_1',
    ###
    'creature1genvolturi2': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi3': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi4': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi5': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi6': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi7': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi8': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi9': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi10': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi11': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi12': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi13': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi14': 'bdGenvolturiBuiltTopNodeN_1',
    'creature1genvolturi15': 'bdGenvolturiBuiltTopNodeN_1',
    }

VAMP_NAMESPACES = {
    'creature1genvolturi' : 'vamp1',
    'creature1genvolturi2' : 'vamp2',
    'creature1genvolturi3' : 'vamp3',
    'creature1genvolturi4' : 'vamp4',
    'creature1genvolturi5' : 'vamp5',
    'creature1genvolturi6' : 'vamp6',
    'creature1genvolturi7' : 'vamp7',
    'creature1genvolturi8' : 'vamp8',
    'creature1genvolturi9' : 'vamp9',
    'creature1genvolturi10' : 'vamp10',
    'creature1genvolturi11' : 'vamp11',
    'creature1genvolturi12' : 'vamp12',
    'creature1genvolturi13' : 'vamp13',
    'creature1genvolturi14' : 'vamp14',
    'creature1genvolturi15' : 'vamp15',
    }

def getCharacterInfoDict():
    '''
    Returns a dictionary mapping creature names to their official publish names and namespaces.
    '''
    namesDict = dict()
    etcAnniePath = os.getenv('TIP_ANNIE_POSTPROCESS_SCRIPT_PATH')
    fullnamesPod = pod.Pod(os.path.join(etcAnniePath, 'characterNames.pod'))
    namespacePod = pod.Pod(os.path.join(etcAnniePath, 'namespaces.pod'))
    fullnamesNode = fullnamesPod['wolfSettings'].asNode()

    for creature in fullnamesNode.valueNames():
        fullname = fullnamesNode.value(creature).asString()
        if not creature in namesDict:
            namesDict[creature] = {'fullname': fullname}
        else:
            namesDict[creature]['fullname'] = fullname
            
    for creature in namespacePod.valueNames():
        namespace = namespacePod.value(creature).asString()
        if not creature in namesDict:
            namesDict[creature] = {'namespace': namespace}
        else:
            namesDict[creature]['namespace'] = namespace
 
    for creature, namespace in VAMP_NAMESPACES.items():
        if not creature in namesDict:
            namesDict[creature] = {'namespace': namespace}
        else:
            namesDict[creature]['namespace'] = namespace
 
    for creature, color in CHARACTER_COLORS.items():
        if not creature in namesDict:
            namesDict[creature] = {'color': color}
        else:
            namesDict[creature]['color'] = color
             
    for creature, code in CHARACTER_CODES.items():
        if not creature in namesDict:
            namesDict[creature] = {'code': code}
        else:
            namesDict[creature]['code'] = code      

    for creature, topnode in CHARACTER_TOPNODES.items():
        if not creature in namesDict:
            namesDict[creature] = {'topnode': topnode}
        else:
            namesDict[creature]['topnode'] = topnode             
  
    return namesDict
    
    
###################################    
    
NAMES_INFO = getCharacterInfoDict()

###################################
    
    
def getCharacterFromPod(podPath):
    object = GtoGeometryCachePod.fromPodFile(podPath).objects[0]
    for key, value in sorted(NAMES_INFO.iteritems()):
        if 'code' in value:
            if value['code'] in object:
                # Vampire (vamp2+)
                if 'GAV' in value['code']:
                    namespace = object.rpartition(':')[0]
                    if namespace:
                        if namespace[-1].isdigit():
                            index = int(namespace[-1])
                            return VAMP_LIST[index - 1]
                # Wolf (or vamp1)
                return key
                    
                    
    return None

def getCharacterFromCode(code):  
    for key, value in sorted(NAMES_INFO.iteritems()):
        if 'code' in value:
            if value['code'] == code:
                return key
    return None   
    
def getCharacterFromFullname(fullname): 
    for key, value in sorted(NAMES_INFO.iteritems()):
        if 'fullname' in value:
            if value['fullname'] == fullname:
                return key
    return None    
    
    
if __name__ == '__main__':
    import pprint
    foo = getCharacterInfoDict()
    pprint.pprint(foo)
