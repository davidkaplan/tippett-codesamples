//******************************************************************************
// Copyright (c) 2001-2004 Tweak Inc. All rights reserved.
//******************************************************************************

#include "TipPolyRotate.h"

#include <maya/MFnPlugin.h>
#include <maya/MGlobal.h>

//*****************************************************************************
MStatus initializePlugin(MObject obj)
{
   extern const char* TipPolyRotate_VERSIONTAG;
   const char *versionStr = strstr(TipPolyRotate_VERSIONTAG, "SVN");

   MStatus status;
   MFnPlugin plugin(obj, "Tippett", versionStr, "Any");

   status = plugin.registerCommand("TipPolyRotate",
                                   TipPolyRotate::creator,
                                   TipPolyRotate::directionSyntax);

   if (!status)
       status.perror("registerCommand");

   return status;
}

//*****************************************************************************
MStatus uninitializePlugin(MObject obj)
{
   MStatus status;
   MFnPlugin plugin(obj);

   status = plugin.deregisterCommand("TipPolyRotate");
   if (!status)
       status.perror("deregisterCommand");

   return status;
}
