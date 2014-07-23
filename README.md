tippett
=======

Code samples from my work at Tippett Studio (2011-2013).


=========
TipPolyRotate
=========
This Maya plugin provides a means for rotating a polygon's vertex order.  Without modifying the vertices themselves, the plugin modifies the order in which the vertices define the topology of the polygon.  This is useful for certain shaders which require polygon topology to be oriented consistently with neighboring geometry.


=======
animLib
=======
animLib is an animation library instancing tool that I wrote for Breaking Dawn Part II.  The tool consists of a user interface allowing animators to do a lightweight import of a cached geometry sequence, displayed in Maya with a GL viewer plugin.  Upon publishing by the user, the tool sends a job to the farm to recache the geometry with the applied spatial transform, retiming curve, and temporal offset.


=========
playblast
=========
This playblast tool replaced Maya's default playblast functionality.  The significant advantage of this tool is the ability to send playblast jobs to farm machines and batch the frames.  The tool consists of a user interface, and methods to create the farm job, and run the playblasts from display-less farm machines.


=========
podPublish
=========
Pod is a container file format that Tippett uses for geometry caching.  Several plugins were written for publishing pods of different geometry types.  Here, a plugin script publishes a pod of FxRib type by validating the data, ascertaining dependencies, modifying the data in the pod nodes and dependencies, and moving those files to a locked-down area on disk.
