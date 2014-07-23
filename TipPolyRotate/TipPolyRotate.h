//******************************************************************************
// Copyright (c) 2007 Tippett Studio. All rights reserved.
// $Id$
//******************************************************************************

#ifndef __TIP_POLY_ROTATE_H__
#define __TIP_POLY_ROTATE_H__

#include <maya/MObject.h>
#include <maya/MFnMesh.h>
#include <maya/MPxCommand.h>
#include <maya/MSelectionList.h>
#include <maya/MFloatPointArray.h>
#include <maya/MIntArray.h>
#include <maya/MFloatArray.h>
#include <maya/MDagPath.h>
#include <maya/MSyntax.h>

#include <map>
#include <string>

//
// This plugin rotates selected polygons on a mesh
// clockwise or counterclockwise by reordering the
// polygon's vertex indices.
//

typedef std::map<std::string, MIntArray> MapType;  // key=dag pathname, value=vert index array
enum Direction {clockwise, counterClockwise};

class TipPolyRotate : public MPxCommand
{

public:
   unsigned            vertsNum;
   unsigned            polysNum;
   MFloatPointArray    m_pointsArray;
   MIntArray           m_vertsNumArray;
   MDagPath            m_meshDagPath;
   MapType             m_oldMesh;
   Direction           direction;
   
   MStatus             m_hasUVs;
   MFloatArray         m_arrayU;
   MFloatArray         m_arrayV;
   MIntArray           m_uvCountArray;
   MIntArray           m_uvIdArray;
   MString             m_UVSetName;

public:
   TipPolyRotate();
   virtual ~TipPolyRotate();
   static void* creator();
   
   bool isUndoable() const;
   static MSyntax directionSyntax();
   
   MStatus doIt(const MArgList& args);
   MStatus redoIt();
   MStatus undoIt();
private:
   MSelectionList m_selectionList;

   MStatus parseArgs(const MArgList& args);
   void compute();
};

#endif    // End #ifdef __TIP_POLY_ROTATE_H__
