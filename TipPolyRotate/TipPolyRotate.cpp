//******************************************************************************
// Copyright (c) 2007 Tippett Studio. All rights reserved.
// $Id$
//******************************************************************************

#include "TipPolyRotate.h"

#include <maya/MIOStream.h>
#include <maya/MGlobal.h>
#include <maya/MArgList.h>
#include <maya/MSelectionList.h>
#include <maya/MItSelectionList.h>
#include <maya/MObject.h>
#include <maya/MDagPath.h>
#include <maya/MItMeshPolygon.h>
#include <maya/MIntArray.h>
#include <maya/MFloatPointArray.h>
#include <maya/MTypes.h>
#include <maya/MString.h>
#include <maya/MSyntax.h>
#include <maya/MArgDatabase.h>

#include <set>
#include <map>
#include <string>
#include <vector>

//*****************************************************************************
TipPolyRotate::TipPolyRotate()
{
   direction = clockwise;
   m_hasUVs = MStatus::kFailure;
}

TipPolyRotate::~TipPolyRotate() { }

void* TipPolyRotate::creator()
{
   return new TipPolyRotate();
}

bool TipPolyRotate::isUndoable() const
{
  return true;
}

//*****************************************************************************

// Set up flags for clockwise and counterclockwise

#define kCounterClockwiseFlag "-ccw"
#define kCounterClockwiseFlagLong "-counterclockwise"

MSyntax TipPolyRotate::directionSyntax()
{
   MSyntax m_directionFlag;
   m_directionFlag.addFlag(kCounterClockwiseFlag, kCounterClockwiseFlagLong, MSyntax::kBoolean);
   return m_directionFlag;
}

MStatus TipPolyRotate::parseArgs(const MArgList& args)
{
   MArgDatabase argData(syntax(), args);
   bool directionFlagArg = false;
   if (argData.isFlagSet(kCounterClockwiseFlag))
   {
       // let direction = 0 be clockwise
       //     direction = 1 be counterclockwise
       argData.getFlagArgument(kCounterClockwiseFlag, 0, directionFlagArg);
       // clockwise is assumed, so...
       if (directionFlagArg)
       {
           direction = counterClockwise;
       }
   }
   return MS::kSuccess;
}

//*****************************************************************************
MStatus TipPolyRotate::doIt(const MArgList& args)
{
  MGlobal::getActiveSelectionList(m_selectionList);
  parseArgs(args);
  return redoIt();
}

//*****************************************************************************
MStatus TipPolyRotate::redoIt()
{
   MObject m_multiFaceComponent;
   MIntArray  m_vertsIndexArray;

   //if (!m_selectionList.isEmpty())

   // Iterate through each object that has polygons selected
   for (MItSelectionList m_polyIter(m_selectionList, MFn::kMeshPolygonComponent); !m_polyIter.isDone(); m_polyIter.next())
   {  
       // Store the dagPath and object of the current polygon component
       m_polyIter.getDagPath(m_meshDagPath, m_multiFaceComponent);
       
       if (!m_multiFaceComponent.isNull()) // Check that an object is selected
       {
           // Bind functions to current mesh
           MFnMesh m_componentMesh(m_meshDagPath);
           
           // Get vertex properties of current mesh
           vertsNum = m_componentMesh.numVertices();
           polysNum = m_componentMesh.numPolygons();
           m_componentMesh.getPoints(m_pointsArray, MSpace::kObject);
           m_componentMesh.getVertices(m_vertsNumArray, m_vertsIndexArray);
           
           // Save current state for Undo() purposes
           m_oldMesh.insert(MapType::value_type(m_meshDagPath.fullPathName().asChar(), m_vertsIndexArray));

           
           // Save current UV state to reapply after rotate
           m_hasUVs = MStatus::kFailure;    
           m_UVSetName = m_componentMesh.currentUVSetName(&m_hasUVs);
           if (m_hasUVs == MStatus::kSuccess)
           {
               m_componentMesh.getAssignedUVs(m_uvCountArray, m_uvIdArray, &m_UVSetName);
               m_componentMesh.getUVs(m_arrayU, m_arrayV, &m_UVSetName);
               MGlobal::displayInfo("Saving UV data");
           }

           // Iterate through each selected face of the mesh
           for (MItMeshPolygon m_faceIter(m_meshDagPath, m_multiFaceComponent); !m_faceIter.isDone(); m_faceIter.next())
           {
               // Get the vertex index array for the particular polygon
               int faceIndex = m_faceIter.index();
               MIntArray m_tempVertList;
               m_componentMesh.getPolygonVertices(faceIndex, m_tempVertList);
               int len = m_tempVertList.length();
                               
               // Compute the polygon's position in the whole mesh's vertex index array
               int indexOffset = 0;
               for(int p = 0; p < faceIndex; p++)
               {
                   indexOffset += m_vertsNumArray[p];
               }
                               
               // Remove the current polygon's vertices from the array
               for (int v = 0; v < len; v++)
               {
                   // Debug check:  if (m_tempVertList[v] == m_vertsIndexArray[indexOffset])
                   m_vertsIndexArray.remove(indexOffset);
               }
               
               // ROTATE POLYGON (Rotate vertex indices)
               if (direction == clockwise)
               {
                   // CLOCKWISE
                   int moveVert = m_tempVertList[len - 1];
                   m_tempVertList.remove(len - 1);
                   m_tempVertList.insert(moveVert, 0);
               }
               if (direction == counterClockwise)
               {
                   // COUNTERCLOCKWISE
                   int moveVert = m_tempVertList[0];
                   m_tempVertList.remove(0);
                   m_tempVertList.insert(moveVert, len - 1);
               }
               
               // Insert the rotated vertex indices back into the array
               for (int v = (len - 1); v >= 0; v--)
               {
                   m_vertsIndexArray.insert(m_tempVertList[v], indexOffset);
               }
           }
           
           // Swap the current mesh for one with the new vert index array
           m_componentMesh.createInPlace(vertsNum, polysNum, m_pointsArray, m_vertsNumArray, m_vertsIndexArray);
           
           // Rewrite the UV map
           if (m_hasUVs == MStatus::kSuccess)
           {
                m_componentMesh.setUVs(m_arrayU, m_arrayV, &m_UVSetName);  
                m_componentMesh.assignUVs(m_uvCountArray, m_uvIdArray, &m_UVSetName);  
                MGlobal::displayInfo("Reassigning UVs");
           }
           else
           {
               MGlobal::displayWarning("No UVs");
           }
        }
     }
  return MS::kSuccess;
}

// Undo goes through the same steps as doIt(), but replaces the vertIndexArray with the one saved in m_oldMesh
MStatus TipPolyRotate::undoIt()
{
   MIntArray m_oldVertsArray;
   
   for (MItSelectionList m_polyIter(m_selectionList, MFn::kMeshPolygonComponent); !m_polyIter.isDone(); m_polyIter.next())
   {  
       // Set up path to object
       m_polyIter.getDagPath(m_meshDagPath);
       MFnMesh m_componentMesh(m_meshDagPath);
       
       // Get mesh properties
       vertsNum = m_componentMesh.numVertices();
       polysNum = m_componentMesh.numPolygons();
       m_componentMesh.getPoints(m_pointsArray, MSpace::kObject);
       m_componentMesh.getVertices(m_vertsNumArray, m_oldVertsArray); //oldVertsArray is just a placeholder here
       
       // Recall previous order of vertex indices
       MIntArray m_oldVertsArray = m_oldMesh.find(m_meshDagPath.fullPathName().asChar()) -> second; //write actual values into oldVertsArray
       
       // Overwrite the current vertex order with the old one
       m_componentMesh.createInPlace(vertsNum, polysNum, m_pointsArray, m_vertsNumArray, m_oldVertsArray);
       
       // Put back the old UVs
       if (m_hasUVs == MStatus::kSuccess)
       {
           m_componentMesh.setUVs(m_arrayU, m_arrayV, &m_UVSetName);  
           m_componentMesh.assignUVs(m_uvCountArray, m_uvIdArray, &m_UVSetName);
       }            
   }
   return MS::kSuccess;              
}
